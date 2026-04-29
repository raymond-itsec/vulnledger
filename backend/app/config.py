import os
import re
from urllib.parse import quote
from pathlib import Path

from pydantic import Field, field_validator, model_validator
from pydantic.fields import PydanticUndefined
from pydantic_settings import BaseSettings
from dotenv import dotenv_values
import yaml

_ALLOWED_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
_ALLOWED_RUNTIME_MODES = {"development", "production"}
_COMPOSE_FALLBACK_RE = re.compile(r"^\$\{([^}:]+):?-(.*)\}$")
_RAW_ENV_PATH = Path("/run/config/vulnledger.env")
_COMPOSE_PATH = Path("/run/config/docker-compose.yml")


class Settings(BaseSettings):
    app_version: str = "0.2.0"
    runtime_mode: str = "development"
    database_url: str = ""
    postgres_host: str = Field(validation_alias="POSTGRES_HOST")
    postgres_service_port: int = Field(validation_alias="POSTGRES_SERVICE_PORT")
    postgres_user: str = Field(validation_alias="POSTGRES_USER")
    postgres_password: str = Field(validation_alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(validation_alias="POSTGRES_DB")
    log_level: str = "INFO"

    @field_validator("log_level", mode="before")
    @classmethod
    def _normalize_log_level(cls, value: object) -> str:
        normalized = str(value or "").strip().upper()
        if normalized not in _ALLOWED_LOG_LEVELS:
            raise ValueError(
                "FINDINGS_LOG_LEVEL must be one of "
                f"{sorted(_ALLOWED_LOG_LEVELS)} (got {value!r})"
            )
        return normalized
    access_token_expire_minutes: int = 5
    refresh_token_expire_days: int = 7
    refresh_token_family_max_lifetime_days: int = 30
    # None = auto-derive as 2 * refresh_token_family_max_lifetime_days.
    refresh_session_retention_days: int | None = None
    trust_proxy_headers: bool = True
    allowed_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    allowed_methods: list[str] = ["GET", "POST", "PATCH", "DELETE", "OPTIONS"]
    allowed_headers: list[str] = ["Authorization", "Content-Type", "Accept", "If-None-Match"]
    object_storage_endpoint: str = "seaweedfs:8333"
    object_storage_access_key: str
    object_storage_secret_key: str
    object_storage_secure: bool = False
    object_storage_evidence_bucket: str = "finding-attachments"
    object_storage_reports_bucket: str = "generated-reports"
    attachment_max_file_size_mb: int = 25
    report_max_findings: int = 250
    report_max_input_chars: int = 200000
    report_max_output_size_mb: int = 25
    report_retention_days: int = 365
    mailjet_api_key: str = ""
    mailjet_api_secret: str = ""
    mailjet_from_email: str = "noreply@findings.local"
    mailjet_from_name: str = "VulnLedger"
    app_base_url: str = "http://localhost"
    # Rate limiting
    rate_limit_login: str = "5/minute"
    rate_limit_api: str = "60/minute"
    # OIDC SSO (optional -- leave empty to disable)
    oidc_enabled: bool = False
    oidc_client_id: str = ""
    oidc_client_secret: str = ""
    oidc_discovery_url: str = ""
    oidc_redirect_uri: str = ""
    oidc_redirect_uri_allowlist: list[str] = []
    oidc_require_nonce: bool = True
    oidc_default_role: str = "reviewer"
    initial_admin_username: str
    initial_admin_password: str
    initial_admin_email: str
    initial_admin_full_name: str
    clamav_host: str = "clamav"
    clamav_port: int = 3310
    jwt_issuer: str
    jwt_audience: str
    jwt_private_key_pem: str = ""
    jwt_public_key_pem: str = ""
    jwt_private_key_file: str = ""
    jwt_public_key_file: str = ""
    session_hint_cookie_name: str

    model_config = {
        "env_prefix": "FINDINGS_",
        "env_file": ".env",
        "extra": "ignore",
    }

    @field_validator(
        "access_token_expire_minutes",
        "refresh_token_expire_days",
        "report_retention_days",
        "postgres_service_port",
    )
    @classmethod
    def _require_positive(cls, value: int, info) -> int:
        if value <= 0:
            raise ValueError(
                f"FINDINGS_{info.field_name.upper()} must be > 0 (got {value})"
            )
        return value

    @field_validator("refresh_session_retention_days", mode="before")
    @classmethod
    def _empty_optional_int_as_none(cls, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator(
        "postgres_host",
        "postgres_user",
        "postgres_password",
        "postgres_db",
        "object_storage_access_key",
        "object_storage_secret_key",
        "jwt_issuer",
        "jwt_audience",
        "session_hint_cookie_name",
        "initial_admin_username",
        "initial_admin_password",
        "initial_admin_email",
        "initial_admin_full_name",
        mode="before",
    )
    @classmethod
    def _require_non_empty_string(cls, value: object, info) -> str:
        text = str(value or "").strip()
        if not text:
            raise ValueError(f"{info.field_name.upper()} must be set")
        return text

    @model_validator(mode="after")
    def _resolve_database_url(self) -> "Settings":
        username = quote(self.postgres_user, safe="")
        password = quote(self.postgres_password, safe="")
        database = quote(self.postgres_db, safe="")
        self.database_url = (
            f"postgresql+asyncpg://{username}:{password}"
            f"@{self.postgres_host}:{self.postgres_service_port}/{database}"
        )
        return self

    @field_validator("runtime_mode", mode="before")
    @classmethod
    def _normalize_runtime_mode(cls, value: object) -> str:
        normalized = str(value or "").strip().lower()
        if normalized not in _ALLOWED_RUNTIME_MODES:
            raise ValueError(
                "FINDINGS_RUNTIME_MODE must be one of "
                f"{sorted(_ALLOWED_RUNTIME_MODES)} (got {value!r})"
            )
        return normalized

    @field_validator("refresh_token_family_max_lifetime_days")
    @classmethod
    def _check_family_lifetime_range(cls, value: int) -> int:
        if not 7 <= value <= 30:
            raise ValueError(
                "FINDINGS_REFRESH_TOKEN_FAMILY_MAX_LIFETIME_DAYS must be between 7 "
                f"and 30 inclusive (got {value})"
            )
        return value

    @model_validator(mode="after")
    def _resolve_session_retention(self) -> "Settings":
        # Retention is the post-expiry forensic window. It must cover at least
        # two full family lifetimes so that when one family ends we still have
        # the family that replaced it available for audit. Unset -> derive the
        # minimum automatically.
        minimum = 2 * self.refresh_token_family_max_lifetime_days
        if self.refresh_session_retention_days is None:
            self.refresh_session_retention_days = minimum
            return self
        if self.refresh_session_retention_days < minimum:
            raise ValueError(
                "FINDINGS_REFRESH_SESSION_RETENTION_DAYS "
                f"({self.refresh_session_retention_days}) must be >= 2x "
                "FINDINGS_REFRESH_TOKEN_FAMILY_MAX_LIFETIME_DAYS "
                f"({self.refresh_token_family_max_lifetime_days} -> {minimum})"
            )
        return self

    @model_validator(mode="after")
    def _require_rs256_keys(self) -> "Settings":
        private_key_configured = bool(self.jwt_private_key_pem.strip() or self.jwt_private_key_file.strip())
        public_key_configured = bool(self.jwt_public_key_pem.strip() or self.jwt_public_key_file.strip())
        if not private_key_configured or not public_key_configured:
            raise ValueError(
                "RS256 signing requires both FINDINGS_JWT_PRIVATE_KEY_FILE / "
                "FINDINGS_JWT_PUBLIC_KEY_FILE or the matching *_PEM settings."
            )
        return self


settings = Settings()


def get_settings() -> Settings:
    return settings


def _env_name_for_field(field_name: str) -> str:
    field = Settings.model_fields[field_name]
    if isinstance(field.validation_alias, str) and field.validation_alias:
        return field.validation_alias
    env_prefix = Settings.model_config.get("env_prefix", "")
    return f"{env_prefix}{field_name.upper()}"


def _settings_env_names() -> list[str]:
    names: list[str] = []
    for field_name in Settings.model_fields:
        if field_name == "database_url":
            continue
        names.append(_env_name_for_field(field_name))
    return sorted(names)


def _raw_env_keys() -> set[str]:
    if not _RAW_ENV_PATH.exists():
        return set()
    values = dotenv_values(_RAW_ENV_PATH)
    return {key for key in values if key}


def _backend_compose_environment() -> dict[str, str]:
    if not _COMPOSE_PATH.exists():
        return {}
    try:
        loaded = yaml.safe_load(_COMPOSE_PATH.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return {}
    services = loaded.get("services") or {}
    backend = services.get("backend") or {}
    environment = backend.get("environment") or {}
    if not isinstance(environment, dict):
        return {}
    normalized: dict[str, str] = {}
    for key, value in environment.items():
        if not isinstance(key, str):
            continue
        normalized[key] = "" if value is None else str(value)
    return normalized


def _has_python_default(env_name: str) -> bool:
    for field_name, field in Settings.model_fields.items():
        if field_name == "database_url":
            continue
        if _env_name_for_field(field_name) != env_name:
            continue
        if field.is_required():
            return False
        return not (field.default is PydanticUndefined and field.default_factory is None)
    return False


def startup_config_source_report() -> dict[str, list[str]]:
    env_names = _settings_env_names()
    raw_env_keys = _raw_env_keys()
    compose_environment = _backend_compose_environment()

    missing_from_env_file: list[str] = []
    compose_fallback: list[str] = []
    python_default: list[str] = []

    for env_name in env_names:
        if env_name in raw_env_keys:
            continue

        missing_from_env_file.append(env_name)

        compose_value = compose_environment.get(env_name, "")
        if env_name in os.environ and _COMPOSE_FALLBACK_RE.match(compose_value):
            compose_fallback.append(env_name)
            continue

        if env_name not in os.environ and _has_python_default(env_name):
            python_default.append(env_name)

    return {
        "missing_from_env_file": sorted(missing_from_env_file),
        "compose_fallback": sorted(compose_fallback),
        "python_default": sorted(python_default),
    }


def applied_default_env_vars() -> list[str]:
    applied: list[str] = []
    for field_name, field in Settings.model_fields.items():
        if field_name == "database_url":
            continue
        if field.is_required():
            continue
        if field.default is PydanticUndefined and field.default_factory is None:
            continue
        env_name = _env_name_for_field(field_name)
        if env_name not in os.environ:
            applied.append(env_name)
    return sorted(applied)
