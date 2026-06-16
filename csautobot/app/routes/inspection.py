import os
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
from services import inspection_service as svc

router = APIRouter(tags=["Inspection"])

# Schemas
class ChecklistItem(BaseModel):
    item: str
    status: str
    note: str = ""

class PresetResponse(BaseModel):
    checklist: List[ChecklistItem]

class DraftRequest(BaseModel):
    target: str
    cycle: str
    checklist: List[ChecklistItem]
    memo: str = ""

class DraftResponse(BaseModel):
    draft_text: str
    summary_json: Any

class LogCreateRequest(BaseModel):
    inspection_id: str
    tenant_id: str = "default_tenant"
    site_id: str
    charger_id: Optional[str] = None
    inspection_cycle: str
    inspection_type: str
    checklist: List[ChecklistItem]
    memo_text: str = ""
    photo_urls: List[str] = []
    ai_summary: Optional[str] = None

@router.get("/inspection/preset", response_model=PresetResponse)
def get_preset_checklist(target: str = "충전기", cycle: str = "월간"):
    presets = svc.preset_checklist(target, cycle)
    checklist = [ChecklistItem(item=x.get("item", ""), status=x.get("status", "정상"), note=x.get("note", "")) for x in presets]
    return PresetResponse(checklist=checklist)

@router.post("/inspection/draft", response_model=DraftResponse)
def create_ai_draft(req: DraftRequest):
    # Convert ChecklistItem list to list of dict
    checklist_dict = [x.model_dump() for x in req.checklist]
    try:
        draft = svc.generate_inspection_draft(
            target=req.target,
            cycle=req.cycle,
            checklist=checklist_dict,
            memo=req.memo
        )
        return DraftResponse(
            draft_text=draft.draft_text,
            summary_json=draft.summary_json
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI draft generation failed: {e}")

@router.post("/inspection/log")
def save_inspection_log(req: LogCreateRequest, db: Session = Depends(get_db)):
    checklist_dict = [x.model_dump() for x in req.checklist]
    try:
        log = repo.create_inspection_log(
            db=db,
            inspection_id=req.inspection_id,
            tenant_id=req.tenant_id,
            site_id=req.site_id,
            charger_id=req.charger_id,
            inspection_cycle=req.inspection_cycle,
            inspection_type=req.inspection_type,
            checklist_json=checklist_dict,
            memo_text=req.memo_text,
            photo_urls_json=req.photo_urls,
            ai_summary=req.ai_summary
        )
        return {"status": "success", "inspection_id": log.inspection_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save inspection log: {e}")

@router.get("/inspection/logs")
def get_all_inspection_logs(limit: int = 1000, db: Session = Depends(get_db)):
    try:
        logs = repo.list_inspection_logs(db=db, limit=limit)
        results = []
        for l in logs:
            results.append({
                "inspection_id": l.inspection_id,
                "tenant_id": l.tenant_id,
                "site_id": l.site_id,
                "site_name": l.site.site_name if l.site else "Unknown Site",
                "charger_id": l.charger_id,
                "charger_model": l.charger.model_name if l.charger else "",
                "inspection_cycle": l.inspection_cycle,
                "inspection_type": l.inspection_type,
                "checklist_json": l.checklist_json,
                "memo_text": l.memo_text,
                "photo_urls_json": l.photo_urls_json,
                "ai_summary": l.ai_summary,
                "status": l.status,
                "created_at": l.created_at.isoformat() if l.created_at else None
            })
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query inspection logs: {e}")

@router.post("/inspection/logs/{inspection_id}/confirm")
def confirm_log(inspection_id: str, confirmed_by: Optional[str] = None, db: Session = Depends(get_db)):
    try:
        log = repo.confirm_inspection_log(db=db, inspection_id=inspection_id, confirmed_by=confirmed_by)
        if not log:
            raise HTTPException(status_code=404, detail="Inspection log not found")
        return {"status": "confirmed", "inspection_id": log.inspection_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to confirm inspection log: {e}")
