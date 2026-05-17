import logging
from pathlib import Path

import yaml
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database import async_session
from app.config import settings
from app.models.finding_template import FindingTemplate
from app.models.user import User
from app.services.auth import hash_password

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"


async def seed_admin_user() -> None:
    async with async_session() as db:
        username = settings.initial_admin_username.strip()
        password = settings.initial_admin_password
        email = settings.initial_admin_email.strip()

        if not username or not password or not email:
            existing_admin = await db.execute(select(User.user_id).where(User.role == "admin").limit(1))
            if existing_admin.scalar_one_or_none():
                return
            logger.warning(
                "Skipping initial admin seed because FINDINGS_INITIAL_ADMIN_USERNAME, "
                "FINDINGS_INITIAL_ADMIN_PASSWORD, or FINDINGS_INITIAL_ADMIN_EMAIL is not set"
            )
            return

        result = await db.execute(select(User).where(User.username == username))
        if result.scalar_one_or_none():
            return

        admin = User(
            username=username,
            password_hash=hash_password(password),
            full_name=settings.initial_admin_full_name,
            email=email,
            role="admin",
            is_active=True,
        )
        db.add(admin)
        try:
            await db.commit()
            logger.info("Seeded initial admin user: %s", username)
        except IntegrityError:
            # Boot race: a sibling backend container committed the seed
            # between our existence check and our insert. The unique
            # constraint on `username` (or `email`) rejects us. Rollback
            # and treat as success - the winner already did the work.
            await db.rollback()
            logger.info(
                "Initial admin seed lost to a concurrent boot (another instance won); continuing"
            )


async def seed_synthetic_user() -> None:
    """Seed the low-privilege monitoring account the synthetic-probe uses.

    Optional: skipped unless all three FINDINGS_SYNTHETIC_USER_* settings
    are provided. The account is a plain `reviewer` (no client link, no
    admin rights) so the probe exercises the real login/refresh/logout
    path without privileged access.
    """
    username = settings.synthetic_user_username.strip()
    password = settings.synthetic_user_password
    email = settings.synthetic_user_email.strip()

    if not username or not password or not email:
        logger.info(
            "Skipping synthetic monitoring user seed "
            "(FINDINGS_SYNTHETIC_USER_* not fully set)"
        )
        return

    async with async_session() as db:
        result = await db.execute(select(User).where(User.username == username))
        if result.scalar_one_or_none():
            return

        probe_user = User(
            username=username,
            password_hash=hash_password(password),
            full_name="Synthetic Monitoring Probe",
            email=email,
            role="reviewer",
            is_active=True,
        )
        db.add(probe_user)
        try:
            await db.commit()
            logger.info("Seeded synthetic monitoring user: %s", username)
        except IntegrityError:
            # Boot race: a sibling backend container committed the seed
            # between our existence check and our insert. Treat as success.
            await db.rollback()
            logger.info(
                "Synthetic user seed lost to a concurrent boot (another instance won); continuing"
            )


async def sync_builtin_templates() -> None:
    if not TEMPLATES_DIR.exists():
        logger.warning("Templates directory not found at %s", TEMPLATES_DIR)
        return

    yaml_files = list(TEMPLATES_DIR.rglob("*.yaml"))
    if not yaml_files:
        logger.info("No template YAML files found")
        return

    async with async_session() as db:
        count_new = 0
        count_updated = 0
        for path in yaml_files:
            try:
                data = yaml.safe_load(path.read_text())
            except Exception:
                logger.warning("Failed to parse template: %s", path)
                continue

            stable_id = data.get("id")
            if not stable_id:
                logger.warning("Template missing 'id' field: %s", path)
                continue

            result = await db.execute(
                select(FindingTemplate).where(FindingTemplate.stable_id == stable_id)
            )
            existing = result.scalar_one_or_none()

            fields = {
                "name": data.get("name", ""),
                "category": data.get("category"),
                "title": data.get("title"),
                "description": data.get("description"),
                "risk_level": data.get("risk_level"),
                "impact": data.get("impact"),
                "recommendation": data.get("recommendation"),
                "references": data.get("references"),
            }

            if existing:
                changed = False
                for key, val in fields.items():
                    if getattr(existing, key) != val:
                        setattr(existing, key, val)
                        changed = True
                if changed:
                    count_updated += 1
            else:
                template = FindingTemplate(
                    stable_id=stable_id,
                    is_builtin=True,
                    **fields,
                )
                db.add(template)
                count_new += 1

        try:
            await db.commit()
            logger.info(
                "Template sync complete: %d new, %d updated", count_new, count_updated
            )
        except IntegrityError:
            # Boot race: a sibling backend container committed the same
            # builtin templates between our per-template existence checks
            # and this commit. The unique constraint on `stable_id`
            # rejects the loser. Rollback and treat as success - the
            # winner already wrote everything.
            await db.rollback()
            logger.info(
                "Builtin template sync lost to a concurrent boot (another instance won); continuing"
            )
