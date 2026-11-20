from sqlalchemy import CheckConstraint

from app.crypto import decrypt_text, encrypt_text
from app.models import Base


EXPECTED_TABLES = {
    "districts", "mandals", "phcs", "gram_panchayats", "villages", "habitations",
    "users", "user_assignments", "patients", "households", "household_members",
    "patient_identifiers", "consents", "habits", "symptoms", "cases", "case_images",
    "media_objects", "ai_models", "ai_inferences", "reviews", "referrals", "appointments",
    "video_sessions", "consult_notes", "investigations", "reports", "diagnoses",
    "treatment_links", "navigator_tasks", "contact_attempts", "transport_requests",
    "notifications", "location_shares", "education_pages", "food_items", "sync_batches",
    "sla_rules", "audit_logs",
}


def test_all_requested_tables_are_registered():
    assert EXPECTED_TABLES <= set(Base.metadata.tables)


def test_pathology_diagnosis_requires_evidence_report():
    constraints = Base.metadata.tables["diagnoses"].constraints
    expressions = [str(item.sqltext) for item in constraints if isinstance(item, CheckConstraint)]
    assert any("pathology_confirmed_malignancy" in expression and "evidence_report_id" in expression
               for expression in expressions)


def test_sensitive_field_encryption_round_trips(monkeypatch):
    import base64

    monkeypatch.setenv("ENCRYPTION_KEY", base64.urlsafe_b64encode(b"x" * 32).decode())
    encrypted = encrypt_text("synthetic example")
    assert b"synthetic example" not in encrypted
    assert decrypt_text(encrypted) == "synthetic example"
