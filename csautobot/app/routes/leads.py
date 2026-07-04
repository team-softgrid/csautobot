import re
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from leads_db import create_lead

router = APIRouter(tags=["Leads"])

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


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
    return LeadCreateResponse(
        id=int(row["id"]),
        status="NEW",
        message="도입 상담 요청이 접수되었습니다. 영업일 1~2일 내 회신드리겠습니다.",
    )
