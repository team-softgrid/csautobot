import os
import sys
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# Setup python path
HERE = Path(__file__).resolve().parent.parent.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from services.quotation_service import generate_quotation_draft, QuotationDraft
from services.ai_provider import AiProviderConfigPayload
from services.tenant_ai_settings import resolve_ai_config_for_request
from storage.db import get_db
from fastapi.responses import StreamingResponse
import io
import openpyxl

router = APIRouter(tags=["Quotation"])

class QuotationRequest(BaseModel):
    query: str = Field(description="고장 증상 및 현상")
    charger_type: str = Field(default="급속", description="충전기 구분: 급속 / 완속")
    tenant_id: str = Field(default="default_tenant", description="테넌트 ID")
    ai_config: AiProviderConfigPayload | None = None

class ExportPartItem(BaseModel):
    part_name: str
    spec: str
    qty: int
    unit_price: int
    category: str

class QuotationExportRequest(BaseModel):
    query: str
    symptom_summary: str
    likely_cause: str
    parts: list[ExportPartItem]
    dispatch_fee: int
    labor_fee: int

@router.post("/quotation/draft", response_model=QuotationDraft)
def create_quotation_draft(req: QuotationRequest, db: Session = Depends(get_db)):
    from services.billing_metering import (
        FEATURE_AI_GENERATION,
        check_quota,
        record_usage,
    )

    tenant_id = (req.tenant_id or "default_tenant").strip()
    check_quota(tenant_id, FEATURE_AI_GENERATION)
    try:
        ai_config = resolve_ai_config_for_request(db, tenant_id, req.ai_config)
    except Exception as cfg_exc:
        print(f"AI config load failed, using env defaults: {cfg_exc}")
        ai_config = None

    try:
        draft = generate_quotation_draft(
            query=req.query,
            charger_type=req.charger_type,
            ai_config=ai_config,
        )
        is_faq = draft.symptom_summary.startswith("FAQ:")
        try:
            record_usage(
                tenant_id,
                FEATURE_AI_GENERATION,
                model_name="faq-shortcut" if is_faq else "hybrid",
                shortcut=is_faq,
            )
        except Exception as usage_exc:
            print(f"Usage metering failed (draft still returned): {usage_exc}")
        return draft
    except HTTPException:
        raise
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 견적서 생성 실패: {str(e)}")

@router.post("/quotation/export")
def export_quotation_excel(req: QuotationExportRequest):
    try:
        template_path = HERE / "assets" / "quotation_template.xlsx"
        if not template_path.is_file():
            raise FileNotFoundError(f"견적서 템플릿 파일을 찾을 수 없습니다: {template_path}")
            
        wb = openpyxl.load_workbook(template_path)
        ws = wb.active
        
        # 1. Fill Header Information
        symptom_clean = req.symptom_summary.replace("접수 증상:", "").strip()
        ws.cell(row=2, column=2).value = f"수  신   : {symptom_clean} 담당 엔지니어 귀하\n주  소   : 현장 점검 대상지"
        
        # 2. Fill Parts and technical fees into the table (starts at row=9, max 8 rows: row 9 to 16)
        all_items = []
        
        # Add parts
        for i, part in enumerate(req.parts, 1):
            all_items.append({
                "no": i,
                "name": part.part_name,
                "spec": part.spec,
                "qty": part.qty,
                "price": part.unit_price,
                "note": part.category
            })
            
        # Add dispatch fee (if greater than 0)
        idx = len(all_items) + 1
        if req.dispatch_fee > 0:
            all_items.append({
                "no": idx,
                "name": "출장 교통비",
                "spec": "기술 서비스료",
                "qty": 1,
                "price": req.dispatch_fee,
                "note": "-"
            })
            idx += 1
            
        # Add labor fee (if greater than 0)
        if req.labor_fee > 0:
            all_items.append({
                "no": idx,
                "name": "작업 공임비",
                "spec": "기술 서비스료",
                "qty": 1,
                "price": req.labor_fee,
                "note": "-"
            })
            
        # Total supply value calculation
        parts_total = sum(p.unit_price * p.qty for p in req.parts)
        supply_value = parts_total + req.dispatch_fee + req.labor_fee
        
        # Fill table rows (row 9 to 16)
        for row_idx in range(9, 17):
            item_idx = row_idx - 9
            if item_idx < len(all_items):
                item = all_items[item_idx]
                ws.cell(row=row_idx, column=2).value = item["no"]
                ws.cell(row=row_idx, column=3).value = item["name"]
                ws.cell(row=row_idx, column=6).value = item["spec"]
                ws.cell(row=row_idx, column=9).value = "EA"
                ws.cell(row=row_idx, column=10).value = item["qty"]
                ws.cell(row=row_idx, column=12).value = item["price"]
                ws.cell(row=row_idx, column=14).value = item["price"] * item["qty"]
                ws.cell(row=row_idx, column=18).value = item["note"]
            else:
                # Clear unused rows in the template
                ws.cell(row=row_idx, column=2).value = ""
                ws.cell(row=row_idx, column=3).value = ""
                ws.cell(row=row_idx, column=6).value = ""
                ws.cell(row=row_idx, column=9).value = ""
                ws.cell(row=row_idx, column=10).value = ""
                ws.cell(row=row_idx, column=12).value = ""
                ws.cell(row=row_idx, column=14).value = ""
                ws.cell(row=row_idx, column=18).value = ""
                
        # 3. Fill Totals
        # 공급가액 총합 (상단, row=7, column=6)
        ws.cell(row=7, column=6).value = supply_value
        
        # 합계 (하단, row=17, column=14)
        ws.cell(row=17, column=14).value = supply_value
        
        # 4. Save to bytes stream
        out = io.BytesIO()
        wb.save(out)
        out.seek(0)
        
        # Return Excel file
        headers = {
            'Content-Disposition': 'attachment; filename="quotation.xlsx"'
        }
        return StreamingResponse(
            out,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=headers
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"엑셀 견적서 생성 실패: {str(e)}")
