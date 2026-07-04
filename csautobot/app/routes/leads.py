import re
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from auth_service import get_current_admin_user
from leads_db import create_lead, list_leads, list_notify_failures, update_lead_status
from services.lead_notifier import notify_new_lead

router = APIRouter(tags=["Leads"])

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
LEAD_STATUSES = ("NEW", "CONTACTED", "CLOSED")


class LeadCreateRequest(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=200)
    contact_name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=5, max_length=200)
    phone: Optional[str] = Field(None, max_length=30)
    interest_plans: List[str] = Field(default_factory=list, max_length=10)
    message: Optional[str] = Field(None, max_length=5000)


class LeadCreateResponse(BaseModel):
    id: int
    status: str
    message: str


class LeadItem(BaseModel):
    id: int
    company_name: str
    contact_name: str
    email: str
    phone: Optional[str] = None
    interest_plans: str
    message: Optional[str] = None
    status: str
    created_at: float


class LeadStatusUpdate(BaseModel):
    status: Literal["NEW", "CONTACTED", "CLOSED"]


class NotifyFailureItem(BaseModel):
    id: int
    lead_id: int | None
    channel: str
    error_message: str
    created_at: float


@router.post("/leads", response_model=LeadCreateResponse, status_code=201)
def submit_lead(body: LeadCreateRequest):
    email = body.email.strip()
    if not EMAIL_PATTERN.match(email):
        raise HTTPException(status_code=422, detail="유효한 이메일 주소를 입력해 주세요.")

    plans = [p.strip() for p in body.interest_plans if p and p.strip()]
    row = create_lead(
        company_name=body.company_name.strip(),
        contact_name=body.contact_name.strip(),
        email=email,
        phone=body.phone.strip() if body.phone else None,
        interest_plans=plans,
        message=body.message.strip() if body.message else None,
    )
    notify_new_lead(dict(row))
    return LeadCreateResponse(
        id=int(row["id"]),
        status="NEW",
        message="도입 상담 요청이 접수되었습니다. 영업일 1~2일 내 회신드리겠습니다.",
    )


@router.get("/leads", response_model=List[LeadItem])
def get_leads(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    _admin: dict = Depends(get_current_admin_user),
):
    rows = list_leads(limit=limit, offset=offset)
    return [LeadItem(**row) for row in rows]


@router.patch("/leads/{lead_id}", response_model=LeadItem)
def patch_lead_status(
    lead_id: int,
    body: LeadStatusUpdate,
    _admin: dict = Depends(get_current_admin_user),
):
    row = update_lead_status(lead_id, body.status)
    if not row:
        raise HTTPException(status_code=404, detail="Lead not found")
    return LeadItem(**row)


@router.get("/leads/notify-failures", response_model=List[NotifyFailureItem])
def get_notify_failures(
    limit: int = Query(default=50, ge=1, le=200),
    _admin: dict = Depends(get_current_admin_user),
):
    rows = list_notify_failures(limit=limit)
    return [NotifyFailureItem(**row) for row in rows]
