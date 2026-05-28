import logging
from datetime import date

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import AnalyticsRecord

logger = logging.getLogger(__name__)


async def upsert_daily_analytics(
    db: AsyncSession,
    tenant_id: str,
    record_date: date,
    fuel_consumed: float = 0.0,
    revenue: float = 0.0,
) -> None:
    """
    Safely upserts the daily analytics record. If the record for the given tenant and date
    does not exist, it inserts it. If it does exist, it adds the provided fuel and revenue
    to the existing totals using an atomic database operation.
    """
    if fuel_consumed == 0.0 and revenue == 0.0:
        return

    try:
        stmt = insert(AnalyticsRecord).values(
            tenant_id=tenant_id,
            date=record_date,
            total_fuel_consumption=fuel_consumed,
            total_revenue=revenue,
        )

        # On conflict, update by adding to the existing values
        stmt = stmt.on_conflict_do_update(
            index_elements=["tenant_id", "date"],
            set_={
                "total_fuel_consumption": AnalyticsRecord.total_fuel_consumption
                + stmt.excluded.total_fuel_consumption,
                "total_revenue": AnalyticsRecord.total_revenue
                + stmt.excluded.total_revenue,
            },
        )

        await db.execute(stmt)
    except Exception as e:
        logger.error(
            f"Failed to upsert daily analytics for tenant {tenant_id} on {record_date}: {e}"
        )
