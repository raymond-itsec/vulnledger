from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import async_session
from app.models.taxonomy import TaxonomyEntry, TaxonomyVersion

DEFAULT_TAXONOMY = {
    "risk_level": [
        {"value": "critical", "label": "Critical", "sort_order": 0, "color": "#dc2626"},
        {"value": "high", "label": "High", "sort_order": 1, "color": "#ea580c"},
        {"value": "medium", "label": "Medium", "sort_order": 2, "color": "#d97706"},
        {"value": "low", "label": "Low", "sort_order": 3, "color": "#2563eb"},
        {
            "value": "informational",
            "label": "Informational",
            "sort_order": 4,
            "color": "#6b7280",
        },
    ],
    "remediation_status": [
        {"value": "open", "label": "Open", "sort_order": 0, "color": "#dc2626"},
        {
            "value": "in_progress",
            "label": "In Progress",
            "sort_order": 1,
            "color": "#ca8a04",
        },
        {"value": "resolved", "label": "Resolved", "sort_order": 2, "color": "#16a34a"},
        {
            "value": "accepted_risk",
            "label": "Accepted Risk",
            "sort_order": 3,
            "color": "#6b7280",
        },
        {
            "value": "false_positive",
            "label": "False Positive",
            "sort_order": 4,
            "color": "#9333ea",
        },
    ],
    "session_status": [
        {"value": "planned", "label": "Planned", "sort_order": 0, "color": "#6b7280"},
        {
            "value": "in_progress",
            "label": "In Progress",
            "sort_order": 1,
            "color": "#ca8a04",
        },
        {
            "value": "completed",
            "label": "Completed",
            "sort_order": 2,
            "color": "#16a34a",
        },
        {
            "value": "cancelled",
            "label": "Cancelled",
            "sort_order": 3,
            "color": "#dc2626",
        },
    ],
    "asset_type": [
        {
            "value": "repository",
            "label": "Source Code Repository",
            "sort_order": 0,
            "color": None,
        },
        {
            "value": "browser_extension",
            "label": "Browser Extension",
            "sort_order": 1,
            "color": None,
        },
        {
            "value": "web_application",
            "label": "Web Application",
            "sort_order": 2,
            "color": None,
        },
        {"value": "api", "label": "API", "sort_order": 3, "color": None},
        {
            "value": "mobile_app",
            "label": "Mobile App",
            "sort_order": 4,
            "color": None,
        },
        {"value": "other", "label": "Other", "sort_order": 5, "color": None},
    ],
}

SUPPORTED_TAXONOMY_DOMAINS = tuple(DEFAULT_TAXONOMY.keys())


class TaxonomyError(ValueError):
    pass


@dataclass
class TaxonomyBundle:
    version: TaxonomyVersion
    domains: dict[str, list[TaxonomyEntry]]

    def active_entries(self, domain: str) -> list[TaxonomyEntry]:
        return [entry for entry in self.domains.get(domain, []) if entry.is_active]

    def label(self, domain: str, value: str) -> str:
        for entry in self.domains.get(domain, []):
            if entry.value == value:
                return entry.label
        return value.replace("_", " ").title()

    def color(self, domain: str, value: str, default: str | None = None) -> str | None:
        for entry in self.domains.get(domain, []):
            if entry.value == value:
                return entry.color or default
        return default

    def order_map(self, domain: str) -> dict[str, int]:
        return {entry.value: entry.sort_order for entry in self.domains.get(domain, [])}


def _group_entries(version: TaxonomyVersion) -> dict[str, list[TaxonomyEntry]]:
    grouped: dict[str, list[TaxonomyEntry]] = defaultdict(list)
    for entry in version.entries:
        grouped[entry.domain].append(entry)
    for domain_entries in grouped.values():
        domain_entries.sort(key=lambda entry: (entry.sort_order, entry.value))
    return dict(grouped)


async def get_taxonomy_version(
    db: AsyncSession,
    *,
    taxonomy_version_id=None,
    current: bool = False,
) -> TaxonomyBundle:
    query = select(TaxonomyVersion).options(joinedload(TaxonomyVersion.entries))
    if taxonomy_version_id is not None:
        query = query.where(TaxonomyVersion.taxonomy_version_id == taxonomy_version_id)
    elif current:
        query = query.where(TaxonomyVersion.is_current.is_(True))
    else:
        raise ValueError("taxonomy_version_id or current=True is required")

    result = await db.execute(query)
    version = result.unique().scalar_one_or_none()
    if not version:
        raise TaxonomyError("Taxonomy version not found")
    return TaxonomyBundle(version=version, domains=_group_entries(version))


async def get_current_taxonomy(db: AsyncSession) -> TaxonomyBundle:
    return await get_taxonomy_version(db, current=True)


async def ensure_default_taxonomy_version() -> None:
    async with async_session() as db:
        result = await db.execute(select(TaxonomyVersion.taxonomy_version_id).limit(1))
        if result.scalar_one_or_none():
            return

        version = TaxonomyVersion(
            version_number=1,
            description="System default taxonomy",
            is_current=True,
        )
        db.add(version)
        await db.flush()

        for domain, entries in DEFAULT_TAXONOMY.items():
            for entry in entries:
                db.add(
                    TaxonomyEntry(
                        taxonomy_version_id=version.taxonomy_version_id,
                        domain=domain,
                        value=entry["value"],
                        label=entry["label"],
                        sort_order=entry["sort_order"],
                        color=entry.get("color"),
                        is_active=True,
                    )
                )

        await db.commit()


def _validate_domains_payload(domains: dict[str, list]) -> None:
    if set(domains.keys()) != set(SUPPORTED_TAXONOMY_DOMAINS):
        raise TaxonomyError(
            f"domains must contain exactly: {', '.join(SUPPORTED_TAXONOMY_DOMAINS)}"
        )

    for domain, entries in domains.items():
        if not entries:
            raise TaxonomyError(f"{domain} must contain at least one entry")
        seen_values: set[str] = set()
        seen_orders: set[int] = set()
        for entry in entries:
            value = entry.value.strip()
            if value in seen_values:
                raise TaxonomyError(f"{domain} contains duplicate value '{value}'")
            if entry.sort_order in seen_orders:
                raise TaxonomyError(
                    f"{domain} contains duplicate sort_order {entry.sort_order}"
                )
            seen_values.add(value)
            seen_orders.add(entry.sort_order)


async def create_taxonomy_version(
    db: AsyncSession,
    *,
    description: str | None,
    domains: dict[str, list],
    make_current: bool = True,
) -> TaxonomyBundle:
    _validate_domains_payload(domains)

    next_version = (
        await db.execute(select(func.coalesce(func.max(TaxonomyVersion.version_number), 0)))
    ).scalar_one()
    version = TaxonomyVersion(
        version_number=int(next_version) + 1,
        description=description,
        is_current=make_current,
    )
    if make_current:
        await db.execute(update(TaxonomyVersion).values(is_current=False))

    db.add(version)
    await db.flush()

    for domain, entries in domains.items():
        for entry in entries:
            db.add(
                TaxonomyEntry(
                    taxonomy_version_id=version.taxonomy_version_id,
                    domain=domain,
                    value=entry.value.strip(),
                    label=entry.label.strip(),
                    sort_order=entry.sort_order,
                    color=entry.color.strip() if entry.color else None,
                    is_active=entry.is_active,
                )
            )

    await db.commit()
    return await get_taxonomy_version(db, taxonomy_version_id=version.taxonomy_version_id)


async def activate_taxonomy_version(
    db: AsyncSession, taxonomy_version_id
) -> TaxonomyBundle:
    bundle = await get_taxonomy_version(db, taxonomy_version_id=taxonomy_version_id)
    await db.execute(update(TaxonomyVersion).values(is_current=False))
    bundle.version.is_current = True
    await db.commit()
    return await get_taxonomy_version(db, taxonomy_version_id=taxonomy_version_id)


async def require_taxonomy_value(
    db: AsyncSession, domain: str, value: str | None
) -> TaxonomyEntry | None:
    if value is None:
        return None
    bundle = await get_current_taxonomy(db)
    for entry in bundle.active_entries(domain):
        if entry.value == value:
            return entry
    allowed = [entry.value for entry in bundle.active_entries(domain)]
    raise TaxonomyError(f"{domain} must be one of: {allowed}")
