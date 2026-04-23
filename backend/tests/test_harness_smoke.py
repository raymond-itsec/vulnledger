import pytest
from sqlalchemy import text


@pytest.mark.asyncio
async def test_db_session_smoke(db_session):
    result = await db_session.execute(text("SELECT 1"))
    assert result.scalar_one() == 1
