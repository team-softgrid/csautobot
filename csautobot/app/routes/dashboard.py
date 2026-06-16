import sys
from pathlib import Path
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Setup python path
HERE = Path(__file__).resolve().parent.parent.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from storage.db import get_db
from storage import repositories as repo

router = APIRouter(tags=["Dashboard"])

# Schemas
class MetricSummary(BaseModel):
    total_inspections: int
    completed_inspections: int
    draft_inspections: int
    total_feedbacks: int
    avg_rating: float
    avg_usefulness: float

class DashboardStatsResponse(BaseModel):
    metrics: MetricSummary
    inspections: List[Any]
    feedbacks: List[Any]

def _risk_key(ai_sum_raw: Any) -> str:
    import json
    if not ai_sum_raw:
        return "low"
    
    # Try parsing json if it is a string
    ai_dict = {}
    if isinstance(ai_sum_raw, str):
        try:
            ai_dict = json.loads(ai_sum_raw)
        except Exception:
            pass
    elif isinstance(ai_sum_raw, dict):
        ai_dict = ai_sum_raw

    val = str(ai_dict.get("overall_risk") or "").lower()
    for k in ("high", "mid", "low"):
        if k in val:
            return k
    return "low"

@router.get("/dashboard/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(db: Session = Depends(get_db)):
    try:
        # Load raw inspection logs and feedbacks
        logs = repo.list_inspection_logs(db=db, limit=1000)
        feedbacks = repo.list_feedback(db=db, limit=1000)

        total_inspections = len(logs)
        completed_inspections = sum(1 for l in logs if l.status == "confirmed")
        draft_inspections = total_inspections - completed_inspections

        total_feedbacks = len(feedbacks)
        avg_rating = 0.0
        avg_usefulness = 0.0
        if total_feedbacks > 0:
            avg_rating = sum(float(f.rating or 0) for f in feedbacks) / total_feedbacks
            avg_usefulness = sum(float(f.usefulness or 0) for f in feedbacks) / total_feedbacks

        inspections_data = []
        for l in logs:
            inspections_data.append({
                "inspection_id": l.inspection_id,
                "created_at": l.created_at.isoformat() if l.created_at else None,
                "status": l.status or "draft",
                "inspection_type": l.inspection_type or "-",
                "inspection_cycle": l.inspection_cycle or "-",
                "site_name": l.site.site_name if l.site else "-",
                "charger_id": l.charger_id or "-",
                "overall_risk": _risk_key(l.ai_summary)
            })

        feedbacks_data = []
        for f in feedbacks:
            feedbacks_data.append({
                "feedback_id": f.feedback_id,
                "target_type": f.target_type,
                "role": f.role or "기타",
                "rating": f.rating,
                "usefulness": f.usefulness,
                "comment": f.comment or "",
                "created_at": f.created_at.isoformat() if f.created_at else None
            })

        return DashboardStatsResponse(
            metrics=MetricSummary(
                total_inspections=total_inspections,
                completed_inspections=completed_inspections,
                draft_inspections=draft_inspections,
                total_feedbacks=total_feedbacks,
                avg_rating=round(avg_rating, 2),
                avg_usefulness=round(avg_usefulness, 2)
            ),
            inspections=inspections_data,
            feedbacks=feedbacks_data
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load dashboard statistics: {e}")
