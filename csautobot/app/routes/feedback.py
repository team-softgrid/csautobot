import sys
from pathlib import Path
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# Setup python path
HERE = Path(__file__).resolve().parent.parent.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from storage.db import get_db
from storage import repositories as repo

router = APIRouter(tags=["Feedback"])

# Schemas
class FeedbackCreateRequest(BaseModel):
    target_type: str = Field(description="search 또는 draft")
    target_id: Optional[str] = None
    role: str = "기타"
    reviewer_name: Optional[str] = None
    rating: int = Field(ge=1, le=5)
    usefulness: int = Field(ge=1, le=5)
    comment: Optional[str] = None

class FeedbackResponse(BaseModel):
    feedback_id: str
    target_type: str
    target_id: Optional[str]
    role: Optional[str]
    reviewer_name: Optional[str]
    rating: int
    usefulness: int
    comment: Optional[str]
    created_at: Optional[str]

@router.post("/feedbacks")
def save_feedback(req: FeedbackCreateRequest, db: Session = Depends(get_db)):
    try:
        feedback = repo.create_feedback(
            db=db,
            target_type=req.target_type,
            target_id=req.target_id,
            role=req.role,
            reviewer_name=req.reviewer_name,
            rating=req.rating,
            usefulness=req.usefulness,
            comment=req.comment
        )
        return {"status": "success", "feedback_id": feedback.feedback_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create feedback: {e}")

@router.get("/feedbacks", response_model=List[FeedbackResponse])
def get_all_feedbacks(limit: int = 1000, db: Session = Depends(get_db)):
    try:
        feedbacks = repo.list_feedback(db=db, limit=limit)
        results = []
        for f in feedbacks:
            results.append(FeedbackResponse(
                feedback_id=f.feedback_id,
                target_type=f.target_type,
                target_id=f.target_id,
                role=f.role,
                reviewer_name=f.reviewer_name,
                rating=f.rating,
                usefulness=f.usefulness,
                comment=f.comment,
                created_at=f.created_at.isoformat() if f.created_at else None
            ))
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve feedbacks: {e}")
