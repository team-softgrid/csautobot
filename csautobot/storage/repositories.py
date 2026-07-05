import datetime
import json
import uuid
from typing import List, Optional, Any
from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    DateTime,
    Date,
    ForeignKey,
    Numeric,
    JSON,
    Index,
)
from sqlalchemy.orm import Session, relationship, joinedload
from storage.db import Base, get_db_context


# ---------------------------------------------------------------------------
# helper functions
# ---------------------------------------------------------------------------

def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


# ---------------------------------------------------------------------------
# SQLAlchemy Models
# ---------------------------------------------------------------------------

class Tenant(Base):
    __tablename__ = "tenant"
    
    tenant_id = Column(String(50), primary_key=True)
    tenant_name = Column(String(100), nullable=False)
    plan_code = Column(String(50), nullable=False, default="FREE")
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    
    # Relationships
    users = relationship("AppUser", back_populates="tenant", cascade="all, delete-orphan")
    sites = relationship("Site", back_populates="tenant", cascade="all, delete-orphan")
    chargers = relationship("Charger", back_populates="tenant", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="tenant", cascade="all, delete-orphan")
    inspection_logs = relationship("InspectionLog", back_populates="tenant", cascade="all, delete-orphan")
    usage_meters = relationship("UsageMeter", back_populates="tenant", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="tenant", cascade="all, delete-orphan")
    ai_settings = relationship(
        "TenantAiSettings",
        back_populates="tenant",
        cascade="all, delete-orphan",
        uselist=False,
    )


class TenantAiSettings(Base):
    __tablename__ = "tenant_ai_settings"

    tenant_id = Column(String(50), ForeignKey("tenant.tenant_id", ondelete="CASCADE"), primary_key=True)
    provider = Column(String(20), nullable=False, default="hybrid")
    hybrid_providers = Column(JSON, nullable=True)
    models = Column(JSON, nullable=True)
    ollama_base_url = Column(String(255), nullable=False, default="http://localhost:11434")
    credentials_encrypted = Column(Text, nullable=True)
    credential_hints = Column(JSON, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    tenant = relationship("Tenant", back_populates="ai_settings")


class AppUser(Base):
    __tablename__ = "app_user"
    
    user_id = Column(String(50), primary_key=True)
    tenant_id = Column(String(50), ForeignKey("tenant.tenant_id", ondelete="CASCADE"), nullable=False)
    email = Column(String(100), nullable=False)
    role = Column(String(30), nullable=False, default="USER")
    status = Column(String(20), nullable=False, default="ACTIVE")
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")


class Site(Base):
    __tablename__ = "site"
    
    site_id = Column(String(50), primary_key=True)
    tenant_id = Column(String(50), ForeignKey("tenant.tenant_id", ondelete="CASCADE"), nullable=False)
    site_name = Column(String(100), nullable=False)
    operator_name = Column(String(100), default=None)
    address = Column(String(255), default=None)
    region = Column(String(50), default=None)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="sites")
    chargers = relationship("Charger", back_populates="site", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="site")
    inspection_logs = relationship("InspectionLog", back_populates="site", cascade="all, delete-orphan")


class Charger(Base):
    __tablename__ = "charger"
    
    charger_id = Column(String(50), primary_key=True)
    tenant_id = Column(String(50), ForeignKey("tenant.tenant_id", ondelete="CASCADE"), nullable=False)
    site_id = Column(String(50), ForeignKey("site.site_id", ondelete="CASCADE"), nullable=False)
    manufacturer = Column(String(100), default=None)
    model_name = Column(String(100), default=None)
    serial_no = Column(String(100), default=None)
    install_date = Column(Date, default=None)
    status = Column(String(20), nullable=False, default="NORMAL")
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="chargers")
    site = relationship("Site", back_populates="chargers")
    incidents = relationship("Incident", back_populates="charger")
    inspection_logs = relationship("InspectionLog", back_populates="charger")


class Incident(Base):
    __tablename__ = "incident"
    
    incident_id = Column(String(50), primary_key=True)
    tenant_id = Column(String(50), ForeignKey("tenant.tenant_id", ondelete="CASCADE"), nullable=False)
    site_id = Column(String(50), ForeignKey("site.site_id", ondelete="SET NULL"), default=None)
    charger_id = Column(String(50), ForeignKey("charger.charger_id", ondelete="SET NULL"), default=None)
    occurred_at = Column(DateTime, default=None)
    reported_at = Column(DateTime, default=None)
    symptom_raw = Column(Text, nullable=False)
    symptom_norm = Column(Text, default=None)
    error_code_raw = Column(String(50), default=None)
    error_code_norm = Column(String(50), default=None)
    severity = Column(String(20), default=None)
    source_file = Column(String(255), default=None)
    source_sheet = Column(String(100), default=None)
    source_row = Column(Integer, default=None)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="incidents")
    site = relationship("Site", back_populates="incidents")
    charger = relationship("Charger", back_populates="incidents")
    actions = relationship("Action", back_populates="incident", cascade="all, delete-orphan")


class Action(Base):
    __tablename__ = "action"
    
    action_id = Column(String(50), primary_key=True)
    incident_id = Column(String(50), ForeignKey("incident.incident_id", ondelete="CASCADE"), nullable=False)
    action_at = Column(DateTime, default=None)
    action_type = Column(String(50), nullable=False)
    action_detail = Column(Text, nullable=False)
    result = Column(String(50), default=None)
    downtime_min = Column(Integer, default=0)
    engineer_name = Column(String(100), default=None)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    
    # Relationships
    incident = relationship("Incident", back_populates="actions")
    part_usages = relationship("PartUsage", back_populates="action", cascade="all, delete-orphan")


class PartUsage(Base):
    __tablename__ = "part_usage"
    
    part_usage_id = Column(String(50), primary_key=True)
    action_id = Column(String(50), ForeignKey("action.action_id", ondelete="CASCADE"), nullable=False)
    part_code = Column(String(50), default=None)
    part_name = Column(String(100), default=None)
    qty = Column(Integer, default=1)
    unit_cost = Column(Numeric(15, 2), default=0.00)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    
    # Relationships
    action = relationship("Action", back_populates="part_usages")


class InspectionLog(Base):
    __tablename__ = "inspection_log"
    
    inspection_id = Column(String(50), primary_key=True)
    tenant_id = Column(String(50), ForeignKey("tenant.tenant_id", ondelete="CASCADE"), nullable=False)
    site_id = Column(String(50), ForeignKey("site.site_id", ondelete="CASCADE"), nullable=False)
    charger_id = Column(String(50), ForeignKey("charger.charger_id", ondelete="SET NULL"), default=None)
    inspection_cycle = Column(String(20), nullable=False)
    inspection_type = Column(String(30), nullable=False)
    checklist_json = Column(JSON, nullable=False)
    memo_text = Column(Text, default=None)
    photo_urls_json = Column(JSON, default=None)
    ai_summary = Column(JSON, default=None) # Store as JSON directly
    status = Column(String(20), nullable=False, default="DRAFT")
    confirmed_by = Column(String(50), default=None)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="inspection_logs")
    site = relationship("Site", back_populates="inspection_logs")
    charger = relationship("Charger", back_populates="inspection_logs")


class UsageMeter(Base):
    __tablename__ = "usage_meter"
    
    usage_id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), ForeignKey("tenant.tenant_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(50), default=None)
    feature_code = Column(String(50), nullable=False)
    model_name = Column(String(50), default=None)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    request_count = Column(Integer, nullable=False, default=1)
    measured_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="usage_meters")


class AuditLog(Base):
    __tablename__ = "audit_log"
    
    audit_id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), ForeignKey("tenant.tenant_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(50), default=None)
    action_code = Column(String(50), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(50), nullable=False)
    payload_json = Column(JSON, default=None)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="audit_logs")


class Feedback(Base):
    __tablename__ = "feedback"
    
    feedback_id = Column(String(50), primary_key=True)
    target_type = Column(String(50), nullable=False)
    target_id = Column(String(100), default=None)
    role = Column(String(50), nullable=False)
    reviewer_name = Column(String(100), default=None)
    rating = Column(Integer, default=None)
    usefulness = Column(Integer, default=None)
    comment = Column(Text, default=None)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)


# Add indexes
Index('idx_incident_search', Incident.tenant_id, Incident.site_id, Incident.error_code_norm)
Index('idx_inspection_site', InspectionLog.tenant_id, InspectionLog.site_id, InspectionLog.status)
Index('idx_usage_tenant_date', UsageMeter.tenant_id, UsageMeter.measured_at)


# ---------------------------------------------------------------------------
# Repositories (CRUD Helpers)
# ---------------------------------------------------------------------------

class BaseRepository:
    def __init__(self, db: Session):
        self.db = db


class TenantRepository(BaseRepository):
    def get_by_id(self, tenant_id: str) -> Optional[Tenant]:
        return self.db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()

    def create(self, tenant_id: str, tenant_name: str, plan_code: str = "FREE") -> Tenant:
        tenant = Tenant(tenant_id=tenant_id, tenant_name=tenant_name, plan_code=plan_code)
        self.db.add(tenant)
        self.db.flush()
        return tenant


class SiteRepository(BaseRepository):
    def get_by_id(self, site_id: str) -> Optional[Site]:
        return self.db.query(Site).filter(Site.site_id == site_id).first()

    def get_by_name(self, tenant_id: str, site_name: str) -> Optional[Site]:
        return self.db.query(Site).filter(Site.tenant_id == tenant_id, Site.site_name == site_name).first()

    def create(self, site_id: str, tenant_id: str, site_name: str, operator_name: Optional[str] = None, address: Optional[str] = None, region: Optional[str] = None) -> Site:
        site = Site(
            site_id=site_id,
            tenant_id=tenant_id,
            site_name=site_name,
            operator_name=operator_name,
            address=address,
            region=region
        )
        self.db.add(site)
        self.db.flush()
        return site


class ChargerRepository(BaseRepository):
    def get_by_id(self, charger_id: str) -> Optional[Charger]:
        return self.db.query(Charger).filter(Charger.charger_id == charger_id).first()

    def get_by_model(self, tenant_id: str, site_id: str, model_name: str) -> Optional[Charger]:
        return self.db.query(Charger).filter(
            Charger.tenant_id == tenant_id,
            Charger.site_id == site_id,
            Charger.model_name == model_name
        ).first()

    def create(self, charger_id: str, tenant_id: str, site_id: str, manufacturer: Optional[str] = None, model_name: Optional[str] = None, serial_no: Optional[str] = None, install_date: Optional[datetime.date] = None, status: str = "NORMAL") -> Charger:
        charger = Charger(
            charger_id=charger_id,
            tenant_id=tenant_id,
            site_id=site_id,
            manufacturer=manufacturer,
            model_name=model_name,
            serial_no=serial_no,
            install_date=install_date,
            status=status
        )
        self.db.add(charger)
        self.db.flush()
        return charger


class IncidentRepository(BaseRepository):
    def get_by_id(self, incident_id: str) -> Optional[Incident]:
        return self.db.query(Incident).filter(Incident.incident_id == incident_id).first()

    def create(self, incident_id: str, tenant_id: str, site_id: Optional[str] = None, charger_id: Optional[str] = None, occurred_at: Optional[datetime.datetime] = None, reported_at: Optional[datetime.datetime] = None, symptom_raw: str = "", symptom_norm: Optional[str] = None, error_code_raw: Optional[str] = None, error_code_norm: Optional[str] = None, severity: Optional[str] = None, source_file: Optional[str] = None, source_sheet: Optional[str] = None, source_row: Optional[int] = None) -> Incident:
        incident = Incident(
            incident_id=incident_id,
            tenant_id=tenant_id,
            site_id=site_id,
            charger_id=charger_id,
            occurred_at=occurred_at,
            reported_at=reported_at,
            symptom_raw=symptom_raw,
            symptom_norm=symptom_norm,
            error_code_raw=error_code_raw,
            error_code_norm=error_code_norm,
            severity=severity,
            source_file=source_file,
            source_sheet=source_sheet,
            source_row=source_row
        )
        self.db.add(incident)
        self.db.flush()
        return incident


class ActionRepository(BaseRepository):
    def create(self, action_id: str, incident_id: str, action_at: Optional[datetime.datetime] = None, action_type: str = "", action_detail: str = "", result: Optional[str] = None, downtime_min: int = 0, engineer_name: Optional[str] = None) -> Action:
        action = Action(
            action_id=action_id,
            incident_id=incident_id,
            action_at=action_at,
            action_type=action_type,
            action_detail=action_detail,
            result=result,
            downtime_min=downtime_min,
            engineer_name=engineer_name
        )
        self.db.add(action)
        self.db.flush()
        return action


# ---------------------------------------------------------------------------
# Streamlit Functional API (for backward compatibility)
# ---------------------------------------------------------------------------

def _ensure_tenant_row(db: Session, tenant_id: str) -> None:
    tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    if tenant is None:
        db.add(
            Tenant(
                tenant_id=tenant_id,
                tenant_name=tenant_id.replace("_", " ").title(),
                plan_code="FREE",
            )
        )
        db.flush()


def create_inspection_log(
    *,
    tenant_id: str = "default_tenant",
    site_id: str | None = None,
    site_name: str | None = None,
    charger_id: str | None = None,
    manufacturer: str | None = None,
    model_name: str | None = None,
    inspection_type: str,
    inspection_cycle: str | None = None,
    engineer_name: str | None = None,
    checklist: list[dict[str, Any]],
    memo_text: str | None,
    photo_paths: list[str] | None,
    ai_summary: dict[str, Any] | str | None = None,
    ai_model: str | None = None,
    status: str = "draft",
    inspection_id: str | None = None,
) -> str:
    iid = inspection_id or new_id("ins")
    tenant_id = (tenant_id or "default_tenant").strip()

    if isinstance(ai_summary, str):
        try:
            ai_summary = json.loads(ai_summary)
        except json.JSONDecodeError:
            ai_summary = {"text": ai_summary}
    
    with get_db_context() as db:
        _ensure_tenant_row(db, tenant_id)

        # Find or create Site
        site_name_val = site_name or site_id or "Unknown Site"
        site = None
        if site_id:
            site = db.query(Site).filter(Site.tenant_id == tenant_id, Site.site_id == site_id).first()
        if site is None:
            site = db.query(Site).filter(Site.tenant_id == tenant_id, Site.site_name == site_name_val).first()
        if not site:
            resolved_site_id = site_id or new_id("site")
            site = Site(site_id=resolved_site_id, tenant_id=tenant_id, site_name=site_name_val)
            db.add(site)
            db.flush()
            
        # Find or create Charger
        charger = None
        if charger_id or model_name:
            charger_ident = charger_id or model_name
            charger = db.query(Charger).filter(Charger.tenant_id == tenant_id, Charger.charger_id == charger_ident).first()
            if not charger:
                charger = Charger(
                    charger_id=charger_ident,
                    tenant_id=tenant_id,
                    site_id=site.site_id,
                    manufacturer=manufacturer,
                    model_name=model_name
                )
                db.add(charger)
                db.flush()
                
        # Create inspection log
        log = InspectionLog(
            inspection_id=iid,
            tenant_id=tenant_id,
            site_id=site.site_id,
            charger_id=charger.charger_id if charger else None,
            inspection_cycle=inspection_cycle or "DAILY",
            inspection_type=inspection_type,
            checklist_json=checklist,
            memo_text=memo_text,
            photo_urls_json=photo_paths or [],
            ai_summary=ai_summary,
            status=status.upper(),
            confirmed_by=engineer_name
        )
        db.add(log)
        
    return iid


def update_inspection_ai_summary(
    inspection_id: str,
    ai_summary: dict[str, Any],
    ai_model: str | None,
) -> None:
    with get_db_context() as db:
        log = db.query(InspectionLog).filter(InspectionLog.inspection_id == inspection_id).first()
        if log:
            log.ai_summary = ai_summary
            log.updated_at = datetime.datetime.utcnow()


def confirm_inspection_log(inspection_id: str) -> None:
    with get_db_context() as db:
        log = db.query(InspectionLog).filter(InspectionLog.inspection_id == inspection_id).first()
        if log:
            log.status = "CONFIRMED"
            log.updated_at = datetime.datetime.utcnow()


def list_inspection_logs(limit: int = 100) -> list[dict[str, Any]]:
    with get_db_context() as db:
        logs = (
            db.query(InspectionLog)
            .options(joinedload(InspectionLog.site), joinedload(InspectionLog.charger))
            .order_by(InspectionLog.created_at.desc())
            .limit(limit)
            .all()
        )
        
        results = []
        for log in logs:
            results.append({
                "inspection_id": log.inspection_id,
                "site_name": log.site.site_name if log.site else None,
                "charger_id": log.charger_id,
                "manufacturer": log.charger.manufacturer if log.charger else None,
                "model_name": log.charger.model_name if log.charger else None,
                "inspection_type": log.inspection_type,
                "inspection_cycle": log.inspection_cycle,
                "engineer_name": log.confirmed_by,
                "checklist": log.checklist_json,
                "memo_text": log.memo_text,
                "photo_paths": log.photo_urls_json,
                "ai_summary": log.ai_summary,
                "status": log.status.lower(),
                "created_at": log.created_at.isoformat() if log.created_at else None,
                "updated_at": log.updated_at.isoformat() if log.updated_at else None,
            })
    return results


def get_inspection_log(inspection_id: str) -> dict[str, Any] | None:
    with get_db_context() as db:
        log = (
            db.query(InspectionLog)
            .options(joinedload(InspectionLog.site), joinedload(InspectionLog.charger))
            .filter(InspectionLog.inspection_id == inspection_id)
            .first()
        )
        if not log:
            return None
            
        return {
            "inspection_id": log.inspection_id,
            "site_name": log.site.site_name if log.site else None,
            "charger_id": log.charger_id,
            "manufacturer": log.charger.manufacturer if log.charger else None,
            "model_name": log.charger.model_name if log.charger else None,
            "inspection_type": log.inspection_type,
            "inspection_cycle": log.inspection_cycle,
            "engineer_name": log.confirmed_by,
            "checklist": log.checklist_json,
            "memo_text": log.memo_text,
            "photo_paths": log.photo_urls_json,
            "ai_summary": log.ai_summary,
            "status": log.status.lower(),
            "created_at": log.created_at.isoformat() if log.created_at else None,
            "updated_at": log.updated_at.isoformat() if log.updated_at else None,
        }


def create_feedback(
    *,
    target_type: str,
    target_id: str | None,
    role: str,
    reviewer_name: str | None,
    rating: int | None,
    usefulness: int | None,
    comment: str | None,
) -> str:
    fid = new_id("fb")
    with get_db_context() as db:
        fb = Feedback(
            feedback_id=fid,
            target_type=target_type,
            target_id=target_id,
            role=role,
            reviewer_name=reviewer_name,
            rating=rating,
            usefulness=usefulness,
            comment=comment
        )
        db.add(fb)
    return fid


def list_feedback(
    target_type: str | None = None,
    target_id: str | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    with get_db_context() as db:
        q = db.query(Feedback)
        if target_type:
            q = q.filter(Feedback.target_type == target_type)
        if target_id:
            q = q.filter(Feedback.target_id == target_id)
        feedbacks = q.order_by(Feedback.created_at.desc()).limit(limit).all()
        
        results = []
        for fb in feedbacks:
            results.append({
                "feedback_id": fb.feedback_id,
                "target_type": fb.target_type,
                "target_id": fb.target_id,
                "role": fb.role,
                "reviewer_name": fb.reviewer_name,
                "rating": fb.rating,
                "usefulness": fb.usefulness,
                "comment": fb.comment,
                "created_at": fb.created_at.isoformat() if fb.created_at else None
            })
    return results
