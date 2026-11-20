from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class RecordMixin:
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    created_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))


class District(Base, RecordMixin):
    __tablename__ = "districts"
    __table_args__ = (UniqueConstraint("name_en", name="uq_district_name_en"),)

    name_en: Mapped[str] = mapped_column(String(160), nullable=False)
    name_te: Mapped[str] = mapped_column(String(160), nullable=False)
    state_en: Mapped[str] = mapped_column(String(100), nullable=False, default="Andhra Pradesh")
    state_te: Mapped[str] = mapped_column(String(100), nullable=False, default="ఆంధ్రప్రదేశ్")


class Mandal(Base, RecordMixin):
    __tablename__ = "mandals"
    __table_args__ = (UniqueConstraint("district_id", "name_en", name="uq_mandal_district_name"),)

    district_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("districts.id", ondelete="RESTRICT"), nullable=False
    )
    name_en: Mapped[str] = mapped_column(String(160), nullable=False)
    name_te: Mapped[str] = mapped_column(String(160), nullable=False)


class PHC(Base, RecordMixin):
    __tablename__ = "phcs"
    __table_args__ = (UniqueConstraint("mandal_id", "name_en", name="uq_phc_mandal_name"),)

    mandal_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("mandals.id", ondelete="RESTRICT"), nullable=False
    )
    name_en: Mapped[str] = mapped_column(String(180), nullable=False)
    name_te: Mapped[str] = mapped_column(String(180), nullable=False)
    code: Mapped[str | None] = mapped_column(String(40), unique=True)


class GramPanchayat(Base, RecordMixin):
    __tablename__ = "gram_panchayats"
    __table_args__ = (
        UniqueConstraint("mandal_id", "name_en", name="uq_gram_panchayat_mandal_name"),
    )

    mandal_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("mandals.id", ondelete="RESTRICT"), nullable=False
    )
    name_en: Mapped[str] = mapped_column(String(180), nullable=False)
    name_te: Mapped[str] = mapped_column(String(180), nullable=False)


class Village(Base, RecordMixin):
    __tablename__ = "villages"
    __table_args__ = (UniqueConstraint("gram_panchayat_id", "name_en", name="uq_village_gp_name"),)

    gram_panchayat_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("gram_panchayats.id", ondelete="RESTRICT"), nullable=False
    )
    phc_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("phcs.id", ondelete="RESTRICT"), nullable=False
    )
    name_en: Mapped[str] = mapped_column(String(180), nullable=False)
    name_te: Mapped[str] = mapped_column(String(180), nullable=False)
    lat: Mapped[float | None] = mapped_column(Numeric(9, 6))
    lng: Mapped[float | None] = mapped_column(Numeric(9, 6))


class Habitation(Base, RecordMixin):
    __tablename__ = "habitations"
    __table_args__ = (UniqueConstraint("village_id", "name_en", name="uq_habitation_village_name"),)

    village_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("villages.id", ondelete="RESTRICT"), nullable=False
    )
    name_en: Mapped[str] = mapped_column(String(180), nullable=False)
    name_te: Mapped[str] = mapped_column(String(180), nullable=False)
    lat: Mapped[float | None] = mapped_column(Numeric(9, 6))
    lng: Mapped[float | None] = mapped_column(Numeric(9, 6))


class User(Base, RecordMixin):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "role IN ('asha', 'medical_officer', 'specialist', 'navigator', "
            "'hospital_staff', 'district_admin', 'system_admin')",
            name="ck_users_role",
        ),
    )

    username: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    display_name_ciphertext: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    phone_ciphertext: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))


class UserAssignment(Base, RecordMixin):
    __tablename__ = "user_assignments"
    __table_args__ = (
        CheckConstraint(
            "num_nonnulls(district_id, mandal_id, phc_id, village_id) = 1",
            name="ck_assignment_one_scope",
        ),
    )

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    district_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("districts.id", ondelete="RESTRICT")
    )
    mandal_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("mandals.id", ondelete="RESTRICT")
    )
    phc_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("phcs.id", ondelete="RESTRICT")
    )
    village_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("villages.id", ondelete="RESTRICT")
    )


class Patient(Base, RecordMixin):
    __tablename__ = "patients"

    patient_token: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    name_ciphertext: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    phone_ciphertext: Mapped[bytes | None] = mapped_column(LargeBinary)
    address_ciphertext: Mapped[bytes | None] = mapped_column(LargeBinary)
    age_years: Mapped[int | None] = mapped_column(Integer)
    sex: Mapped[str | None] = mapped_column(String(32))
    habitation_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("habitations.id", ondelete="RESTRICT"), nullable=False
    )
    is_synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))


class Household(Base, RecordMixin):
    __tablename__ = "households"

    household_code: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    habitation_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("habitations.id", ondelete="RESTRICT"), nullable=False
    )


class HouseholdMember(Base, RecordMixin):
    __tablename__ = "household_members"
    __table_args__ = (
        UniqueConstraint("household_id", "patient_id", name="uq_household_patient"),
    )

    household_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("households.id", ondelete="RESTRICT"), nullable=False
    )
    patient_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False
    )
    relation: Mapped[str | None] = mapped_column(String(48))


class PatientIdentifier(Base, RecordMixin):
    __tablename__ = "patient_identifiers"
    __table_args__ = (
        UniqueConstraint("identifier_type", "identifier_hash", name="uq_patient_identifier_hash"),
    )

    patient_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False
    )
    identifier_type: Mapped[str] = mapped_column(String(40), nullable=False)
    identifier_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    masked_last_four: Mapped[str | None] = mapped_column(String(4))


class Consent(Base, RecordMixin):
    __tablename__ = "consents"
    __table_args__ = (
        CheckConstraint("status IN ('granted', 'withdrawn', 'declined')", name="ck_consent_status"),
    )

    patient_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False
    )
    consent_type: Mapped[str] = mapped_column(String(48), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    captured_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    granted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))


class Habit(Base, RecordMixin):
    __tablename__ = "habits"

    patient_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False
    )
    habit_type: Mapped[str] = mapped_column(String(48), nullable=False)
    frequency: Mapped[str | None] = mapped_column(String(80))
    duration_months: Mapped[int | None] = mapped_column(Integer)
    notes_ciphertext: Mapped[bytes | None] = mapped_column(LargeBinary)


class Symptom(Base, RecordMixin):
    __tablename__ = "symptoms"

    patient_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False
    )
    symptom_type: Mapped[str] = mapped_column(String(64), nullable=False)
    onset_date: Mapped[date | None] = mapped_column(Date)
    notes_ciphertext: Mapped[bytes | None] = mapped_column(LargeBinary)


class Case(Base, RecordMixin):
    __tablename__ = "cases"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'awaiting_review', 'in_review', 'referred', 'closed')",
            name="ck_case_status",
        ),
    )

    patient_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False
    )
    opened_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    assigned_to: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT")
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'awaiting_review'"))
    priority_score: Mapped[int | None] = mapped_column(Integer)
    summary_ciphertext: Mapped[bytes | None] = mapped_column(LargeBinary)


class MediaObject(Base, RecordMixin):
    __tablename__ = "media_objects"

    storage_key: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    retention_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    encrypted: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))


class CaseImage(Base, RecordMixin):
    __tablename__ = "case_images"

    case_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False
    )
    media_object_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("media_objects.id", ondelete="RESTRICT"), nullable=False
    )
    oral_site: Mapped[str] = mapped_column(String(48), nullable=False)
    quality_state: Mapped[str] = mapped_column(String(32), nullable=False)


class AIModel(Base, RecordMixin):
    __tablename__ = "ai_models"
    __table_args__ = (UniqueConstraint("name", "version_label", name="uq_ai_model_name_version"),)

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    version_label: Mapped[str] = mapped_column(String(80), nullable=False)
    model_card_url: Mapped[str | None] = mapped_column(String(512))
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))


class AIInference(Base, RecordMixin):
    __tablename__ = "ai_inferences"
    __table_args__ = (
        CheckConstraint(
            "state IN ('image_insufficient', 'suspicious_finding_for_clinical_review', "
            "'no_suspicious_finding_by_demo_model')",
            name="ck_ai_inference_state",
        ),
    )

    case_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False
    )
    case_image_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("case_images.id", ondelete="RESTRICT"), nullable=False
    )
    ai_model_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("ai_models.id", ondelete="RESTRICT"), nullable=False
    )
    state: Mapped[str] = mapped_column(String(64), nullable=False)
    output: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    not_for_clinical_use: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))


class Review(Base, RecordMixin):
    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint("decision IN ('agree', 'disagree', 'defer')", name="ck_review_decision"),
    )

    case_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False
    )
    clinician_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    decision: Mapped[str] = mapped_column(String(16), nullable=False)
    reason_ciphertext: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    signed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Referral(Base, RecordMixin):
    __tablename__ = "referrals"

    case_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False
    )
    referred_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    destination_en: Mapped[str] = mapped_column(String(180), nullable=False)
    destination_te: Mapped[str] = mapped_column(String(180), nullable=False)
    urgency: Mapped[str] = mapped_column(String(32), nullable=False)
    opaque_qr_token_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)


class Appointment(Base, RecordMixin):
    __tablename__ = "appointments"

    case_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False
    )
    patient_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False
    )
    clinician_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT")
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'scheduled'"))


class VideoSession(Base, RecordMixin):
    __tablename__ = "video_sessions"

    appointment_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("appointments.id", ondelete="RESTRICT"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recording_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))


class ConsultNote(Base, RecordMixin):
    __tablename__ = "consult_notes"

    case_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False
    )
    author_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    body_ciphertext: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Investigation(Base, RecordMixin):
    __tablename__ = "investigations"

    case_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False
    )
    investigation_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Report(Base, RecordMixin):
    __tablename__ = "reports"

    investigation_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("investigations.id", ondelete="RESTRICT"), nullable=False
    )
    media_object_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("media_objects.id", ondelete="RESTRICT"), nullable=False
    )
    reviewed_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT")
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Diagnosis(Base, RecordMixin):
    __tablename__ = "diagnoses"
    __table_args__ = (
        CheckConstraint(
            "category <> 'pathology_confirmed_malignancy' OR evidence_report_id IS NOT NULL",
            name="ck_diagnosis_malignancy_requires_report",
        ),
    )

    case_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False
    )
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    clinician_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    evidence_report_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("reports.id", ondelete="RESTRICT")
    )
    signed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TreatmentLink(Base, RecordMixin):
    __tablename__ = "treatment_links"

    diagnosis_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("diagnoses.id", ondelete="RESTRICT"), nullable=False
    )
    facility_en: Mapped[str] = mapped_column(String(180), nullable=False)
    facility_te: Mapped[str] = mapped_column(String(180), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)


class NavigatorTask(Base, RecordMixin):
    __tablename__ = "navigator_tasks"

    case_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False
    )
    assigned_to: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    title_en: Mapped[str] = mapped_column(String(180), nullable=False)
    title_te: Mapped[str] = mapped_column(String(180), nullable=False)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'open'"))


class ContactAttempt(Base, RecordMixin):
    __tablename__ = "contact_attempts"

    navigator_task_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("navigator_tasks.id", ondelete="RESTRICT"), nullable=False
    )
    attempted_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    outcome: Mapped[str] = mapped_column(String(48), nullable=False)
    notes_ciphertext: Mapped[bytes | None] = mapped_column(LargeBinary)


class TransportRequest(Base, RecordMixin):
    __tablename__ = "transport_requests"

    case_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False
    )
    patient_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False
    )
    requested_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'requested'"))
    pickup_address_ciphertext: Mapped[bytes | None] = mapped_column(LargeBinary)


class Notification(Base, RecordMixin):
    __tablename__ = "notifications"

    patient_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False
    )
    user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT")
    )
    channel: Mapped[str] = mapped_column(String(24), nullable=False)
    template_key: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class LocationShare(Base, RecordMixin):
    __tablename__ = "location_shares"

    patient_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False
    )
    consent_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("consents.id", ondelete="RESTRICT"), nullable=False
    )
    latitude: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)
    longitude: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class EducationPage(Base, RecordMixin):
    __tablename__ = "education_pages"
    __table_args__ = (UniqueConstraint("slug", name="uq_education_page_slug"),)

    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    title_en: Mapped[str] = mapped_column(String(200), nullable=False)
    title_te: Mapped[str] = mapped_column(String(200), nullable=False)
    body_en: Mapped[str] = mapped_column(Text, nullable=False)
    body_te: Mapped[str] = mapped_column(Text, nullable=False)


class FoodItem(Base, RecordMixin):
    __tablename__ = "food_items"

    education_page_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("education_pages.id", ondelete="RESTRICT"), nullable=False
    )
    name_en: Mapped[str] = mapped_column(String(160), nullable=False)
    name_te: Mapped[str] = mapped_column(String(160), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(512))
    image_attribution: Mapped[str | None] = mapped_column(String(512))


class SyncBatch(Base, RecordMixin):
    __tablename__ = "sync_batches"
    __table_args__ = (UniqueConstraint("user_id", "client_batch_id", name="uq_sync_batch_client"),)

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    client_batch_id: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    result: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))


class SLARule(Base, RecordMixin):
    __tablename__ = "sla_rules"
    __table_args__ = (UniqueConstraint("event_type", name="uq_sla_event_type"),)

    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    target_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))


class AuditLog(Base, RecordMixin):
    __tablename__ = "audit_logs"

    actor_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT")
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
