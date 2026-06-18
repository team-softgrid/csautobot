import os
import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# Setup python path
HERE = Path(__file__).resolve().parent.parent.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from services.quotation_service import generate_quotation_draft, QuotationDraft

router = APIRouter(tags=["Quotation"])

class QuotationRequest(BaseModel):
    query: str = Field(description="고장 증상 및 현상")
    charger_type: str = Field(default="급속", description="충전기 구분: 급속 / 완속")

@router.post("/quotation/draft", response_model=QuotationDraft)
def create_quotation_draft(req: QuotationRequest):
    try:
        draft = generate_quotation_draft(
            query=req.query,
            charger_type=req.charger_type
        )
        return draft
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 견적서 생성 실패: {str(e)}")
