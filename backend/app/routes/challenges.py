from fastapi import APIRouter, HTTPException, status

from app.challenges import DEMO_CHALLENGES
from app.schemas import ChallengeRead

router = APIRouter(prefix="/challenges", tags=["challenges"])


@router.get("", response_model=list[ChallengeRead])
def list_challenges() -> list[ChallengeRead]:
    return DEMO_CHALLENGES


@router.get("/{challenge_id}", response_model=ChallengeRead)
def get_challenge(challenge_id: str) -> ChallengeRead:
    for challenge in DEMO_CHALLENGES:
        if challenge.id == challenge_id:
            return challenge
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found")
