from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings

_ALLOWED_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


class Settings(BaseSettings):
    app_version: str = "0.1.15"
    database_url: str = "postgresql+asyncpg://findings:findings@db:5432/findings"
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
    trust_proxy_headers: bool = True
    allowed_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = ""
    minio_secret_key: str = ""
    minio_secure: bool = False
    minio_evidence_bucket: str = "finding-attachments"
    minio_reports_bucket: str = "generated-reports"
    attachment_max_file_size_mb: int = 25
    report_max_findings: int = 250
    report_max_input_chars: int = 200000
    report_max_output_size_mb: int = 25
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
    oidc_default_role: str = "reviewer"
    initial_admin_username: str = ""
    initial_admin_password: str = ""
    initial_admin_email: str = ""
    initial_admin_full_name: str = "Administrator"
    # ClamAV (optional -- leave empty to disable)
    clamav_host: str = ""
    clamav_port: int = 3310

    model_config = {
        "env_prefix": "FINDINGS_",
        "env_file": ".env",
        "extra": "ignore",
    }

    @field_validator(
        "access_token_expire_minutes",
        "refresh_token_expire_days",
    )
    @classmethod
    def _require_positive(cls, value: int, info) -> int:
        if value <= 0:
            raise ValueError(
                f"FINDINGS_{info.field_name.upper()} must be > 0 (got {value})"
            )
        return value

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
