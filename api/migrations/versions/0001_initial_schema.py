"""Create Aarogya Drishti schema and data-protection triggers.

Revision ID: 0001_initial_schema
Revises:
"""
from alembic import op

from app.models import Base

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


APPEND_ONLY_TABLES = ("ai_inferences", "audit_logs")
NO_HARD_DELETE_TABLES = (
    "patients",
    "households",
    "household_members",
    "patient_identifiers",
    "consents",
    "habits",
    "symptoms",
    "cases",
    "case_images",
    "media_objects",
    "reviews",
    "referrals",
    "appointments",
    "video_sessions",
    "consult_notes",
    "investigations",
    "reports",
    "diagnoses",
    "treatment_links",
    "navigator_tasks",
    "contact_attempts",
    "transport_requests",
    "notifications",
    "location_shares",
)


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)
    op.execute(
        """
        CREATE FUNCTION reject_immutable_row_mutation() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'Rows in % are immutable; create a new version instead.', TG_TABLE_NAME
                USING ERRCODE = '55000';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE FUNCTION reject_clinical_hard_delete() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'Rows in % cannot be hard-deleted.', TG_TABLE_NAME
                USING ERRCODE = '55000';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    for table in APPEND_ONLY_TABLES:
        op.execute(
            f"CREATE TRIGGER {table}_immutable BEFORE UPDATE OR DELETE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION reject_immutable_row_mutation()"
        )
    for table in NO_HARD_DELETE_TABLES:
        op.execute(
            f"CREATE TRIGGER {table}_no_hard_delete BEFORE DELETE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION reject_clinical_hard_delete()"
        )


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
    op.execute("DROP FUNCTION IF EXISTS reject_immutable_row_mutation()")
    op.execute("DROP FUNCTION IF EXISTS reject_clinical_hard_delete()")
