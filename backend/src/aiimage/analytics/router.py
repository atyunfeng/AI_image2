from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.analytics.schemas import CostReportResponse
from aiimage.analytics.service import build_cost_report
from aiimage.api.dependencies import get_session
from aiimage.auth.dependencies import require_roles
from aiimage.auth.models import Role, User

router = APIRouter(prefix="/analytics", tags=["analytics"])
AnalyticsUser = Annotated[User, Depends(require_roles(Role.ADMIN, Role.OPERATOR))]


@router.get("/costs", response_model=CostReportResponse)
async def cost_report(
    user: AnalyticsUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
    provider: Annotated[str | None, Query(max_length=50)] = None,
    platform_slug: Annotated[str | None, Query(max_length=100)] = None,
    sku: Annotated[str | None, Query(max_length=100)] = None,
) -> CostReportResponse:
    del user
    return await build_cost_report(
        session,
        date_from=date_from,
        date_to=date_to,
        provider=provider,
        platform_slug=platform_slug,
        sku=sku,
    )

