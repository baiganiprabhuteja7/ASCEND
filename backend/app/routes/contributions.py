from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Contribution, User
from app.schemas import ContributionCreate, ContributionRead

router = APIRouter(prefix="/contributions", tags=["contributions"])


@router.post("", response_model=ContributionRead, status_code=status.HTTP_201_CREATED)
def create_contribution(
    payload: ContributionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Contribution:
    data = payload.model_dump()
    if data["evidence_url"] is not None:
        data["evidence_url"] = str(data["evidence_url"])
    contribution = Contribution(user_id=user.id, **data)
    db.add(contribution)
    db.commit()
    db.refresh(contribution)
    return contribution


@router.get("", response_model=list[ContributionRead])
def list_contributions(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Contribution]:
    return list(
        db.scalars(
            select(Contribution)
            .where(Contribution.user_id == user.id)
            .order_by(Contribution.created_at.desc())
        ).all()
    )


@router.get("/{contribution_id}", response_model=ContributionRead)
def get_contribution(
    contribution_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Contribution:
    contribution = db.scalar(
        select(Contribution).where(
            Contribution.id == contribution_id,
            Contribution.user_id == user.id,
        )
    )
    if contribution is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contribution not found")
    return contribution


@router.delete("/{contribution_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contribution(
    contribution_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    contribution = db.scalar(
        select(Contribution).where(
            Contribution.id == contribution_id,
            Contribution.user_id == user.id,
        )
    )
    if contribution is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contribution not found")
    db.delete(contribution)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
