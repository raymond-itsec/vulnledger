from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings

_ALLOWED_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
_ALLOWED_JWT_ALGORITHMS = {"HS256", "RS256"}
_ALLOWED_RUNTIME_MODES = {"development", "production"}


class Settings(BaseSettings):
    app_version: str = "0.2.0"
    runtime_mode: str = "development"
    database_url: str
    secret_key: str = ""
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
    trust_proxy_headers: bool = False
    allowed_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    allowed_methods: list[str] = ["GET", "POST", "PATCH", "DELETE", "OPTIONS"]
    allowed_headers: list[str] = ["Authorization", "Content-Type", "Accept", "If-None-Match"]
    object_storage_endpoint: str = "seaweedfs:8333"
    object_storage_access_key: str = ""
    object_storage_secret_key: str = ""
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
    mailjet_from_name: str = "Security Findings Manager"
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
    initial_admin_username: str = ""
    initial_admin_password: str = ""
    initial_admin_email: str = ""
    initial_admin_full_name: str = "Administrator"
    # ClamAV (optional -- leave empty to disable)
    clamav_host: str = ""
    clamav_port: int = 3310
    # JWT migration controls. Default stays HS256-compatible until RS256 keys are configured.
    jwt_primary_algorithm: str = "HS256"
    jwt_allow_legacy_hs256: bool = True
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
    )
    @classmethod
    def _require_positive(cls, value: int, info) -> int:
        if value <= 0:
            raise ValueError(
                f"FINDINGS_{info.field_name.upper()} must be > 0 (got {value})"
            )
        return value

    @field_validator(
        "database_url",
        "jwt_issuer",
        "jwt_audience",
        "session_hint_cookie_name",
        mode="before",
    )
    @classmethod
    def _require_non_empty_string(cls, value: object, info) -> str:
        text = str(value or "").strip()
        if not text:
            raise ValueError(f"FINDINGS_{info.field_name.upper()} must be set")
        return text

    @field_validator("jwt_primary_algorithm", mode="before")
    @classmethod
    def _normalize_jwt_algorithm(cls, value: object) -> str:
        normalized = str(value or "").strip().upper()
        if normalized not in _ALLOWED_JWT_ALGORITHMS:
            raise ValueError(
                "FINDINGS_JWT_PRIMARY_ALGORITHM must be one of "
                f"{sorted(_ALLOWED_JWT_ALGORITHMS)} (got {value!r})"
            )
        return normalized

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


settings = Settings()


def get_settings() -> Settings:
    return settings
