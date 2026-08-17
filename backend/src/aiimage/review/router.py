from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from aiimage.api.dependencies import get_session
from aiimage.auth.dependencies import require_roles
from aiimage.auth.models import Role, User
from aiimage.review.schemas import ReviewRequest, ReviewResponse
from aiimage.review.service import ReviewConflictError, review_batch

router = APIRouter(prefix="/batches", tags=["review"])
Reviewer = Annotated[User, Depends(require_roles(Role.ADMIN, Role.REVIEWER))]


@router.post("/{batch_id}/review", response_model=ReviewResponse)
async def review_batch_endpoint(
    batch_id: UUID,
    payload: ReviewRequest,
    user: Reviewer,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ReviewResponse:
    try:
        decision = await review_batch(
            session,
            batch_id=batch_id,
            reviewer_user_id=user.id,
            payload=payload,
        )
    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found") from error
    except ReviewConflictError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    return ReviewResponse.model_validate(decision)
