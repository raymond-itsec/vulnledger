import logging
from pathlib import Path

import yaml
from sqlalchemy import select

from app.database import async_session
from app.models.finding_template import FindingTemplate
from app.models.user import User
from app.services.auth import hash_password

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"


async def seed_admin_user() -> None:
    async with async_session() as db:
        result = await db.execute(select(User).where(User.username == "admin"))
        if result.scalar_one_or_none():
            return
        admin = User(
            username="admin",
            password_hash=hash_password("changeme"),
            full_name="Administrator",
            email="admin@localhost",
            role="admin",
            is_active=True,
        )
        db.add(admin)
        await db.commit()
        logger.info("Seeded default admin user (username: admin, password: changeme)")


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

        await db.commit()
        logger.info(
            "Template sync complete: %d new, %d updated", count_new, count_updated
        )
