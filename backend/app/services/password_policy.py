"""Shared password-strength policy used by every entry point that
accepts a new password (onboarding, admin user create / update, future
password-change endpoints).

Combines:
- Length bounds from settings (min / max).
- zxcvbn score floor from settings. zxcvbn is pattern-aware: it
  catches long-but-weak passwords like 'aaaaaaaaaaaaaaaa' or
  'passwordpassword' that would slip past a length-only check.

Future hardening tracked in #33 (longer min, breach-corpus check).
"""

from zxcvbn import zxcvbn

from app.config import settings


def validate_password_strength(
    password: str,
    *,
    user_inputs: list[str | None] | None = None,
) -> None:
    """Raise ValueError if the password fails the policy.

    user_inputs are passed to zxcvbn so the user's own username, email,
    full name etc. are treated as dictionary words (catches passwords
    like 'john_doe2024' for user john_doe).

    Length bounds are also enforced here so callers don't have to know
    where the source of truth lives. Pydantic Field(min_length, ...)
    is intentionally NOT used in caller schemas: keeping policy
    centralised here means the constants flow from a single settings
    source and the error messages stay consistent.
    """
    if len(password) < settings.password_min_length:
        raise ValueError(
            f"Password must be at least {settings.password_min_length} characters."
        )
    if len(password) > settings.password_max_length:
        raise ValueError(
            f"Password must be at most {settings.password_max_length} characters."
        )

    sanitized_inputs = [s for s in (user_inputs or []) if s]
    result = zxcvbn(password, user_inputs=sanitized_inputs)
    if result["score"] < settings.password_min_zxcvbn_score:
        feedback = result.get("feedback") or {}
        warning = feedback.get("warning") or ""
        suggestions = feedback.get("suggestions") or []
        msg = "Password is too weak."
        if warning:
            msg = f"{msg} {warning}"
        if suggestions:
            msg = f"{msg} Suggestions: {'; '.join(suggestions)}"
        raise ValueError(msg)
