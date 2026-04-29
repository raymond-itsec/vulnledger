from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID

from app.services.reports import generate_csv


class _TaxonomyStub:
    def order_map(self, _kind: str) -> dict[str, int]:
        return {}

    def label(self, _kind: str, value: str) -> str:
        return value


def test_generate_csv_neutralizes_formula_like_cells() -> None:
    session = SimpleNamespace(review_name="Session 1", notes=None)
    finding = SimpleNamespace(
        finding_id=UUID("11111111-1111-1111-1111-111111111111"),
        title="=2+2",
        risk_level="high",
        remediation_status="open",
        description="+SUM(A1:A2)",
        impact="-cmd|' /C calc'!A0",
        recommendation="@SUM(1+1)",
        references=["=HYPERLINK(\"http://evil.test\")"],
        created_at=datetime(2026, 4, 29, tzinfo=timezone.utc),
    )

    data = generate_csv(session, [finding], _TaxonomyStub())
    rows = list(csv.reader(io.StringIO(data.decode("utf-8"))))

    assert rows[1][1] == "'=2+2"
    assert rows[1][6] == "'+SUM(A1:A2)"
    assert rows[1][7] == "'-cmd|' /C calc'!A0"
    assert rows[1][8] == "'@SUM(1+1)"
    assert rows[1][9] == "'=HYPERLINK(\"http://evil.test\")"
