from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://findings:findings@db:5432/findings"
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    allowed_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    mailjet_api_key: str = ""
    mailjet_api_secret: str = ""
    mailjet_from_email: str = "noreply@findings.local"
    mailjet_from_name: str = "Security Findings Manager"
    app_base_url: str = "http://localhost"
    # Rate limiting
    rate_limit_login: str = "5/minute"
    rate_limit_api: str = "60/minute"
    # OIDC SSO (optional — leave empty to disable)
    oidc_enabled: bool = False
    oidc_client_id: str = ""
    oidc_client_secret: str = ""
    oidc_discovery_url: str = ""
    oidc_redirect_uri: str = ""
    oidc_default_role: str = "reviewer"
    # ClamAV (optional — leave empty to disable)
    clamav_host: str = ""
    clamav_port: int = 3310

    model_config = {"env_prefix": "FINDINGS_", "env_file": ".env"}


settings = Settings()
