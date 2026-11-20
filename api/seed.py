import hashlib
import secrets
from datetime import datetime, timezone

from sqlalchemy import select

from app.crypto import encrypt_text
from app.db import SessionLocal
from app.models import (
    AIModel,
    Case,
    Consent,
    District,
    GramPanchayat,
    Habitation,
    Habit,
    Household,
    HouseholdMember,
    Mandal,
    Patient,
    PHC,
    Symptom,
    User,
    UserAssignment,
    Village,
)

MANDALS = (
    ("Paderu", "పాడేరు", "PAD"),
    ("Araku Valley", "అరకులోయ", "ARA"),
    ("Ananthagiri", "అనంతగిరి", "ANA"),
    ("Chintapalle", "చింతపల్లి", "CHI"),
    ("Dumbriguda", "డుంబ్రిగూడ", "DUM"),
    ("G. Madugula", "జి. మాడుగుల", "GMD"),
    ("Gudem Kotha Veedhi", "గూడెం కొత్తవీధి", "GKV"),
    ("Hukumpeta", "హుకుంపేట", "HUK"),
    ("Koyyuru", "కొయ్యూరు", "KOY"),
    ("Munchingput", "ముంచింగిపుట్", "MUN"),
    ("Pedabayalu", "పెదబయలు", "PED"),
)

ROLES = (
    ("demo.asha", "asha", "Synthetic ASHA Account"),
    ("demo.medical-officer", "medical_officer", "Synthetic Medical Officer"),
    ("demo.specialist", "specialist", "Synthetic Specialist"),
    ("demo.navigator", "navigator", "Synthetic Patient Navigator"),
    ("demo.hospital-staff", "hospital_staff", "Synthetic Hospital Staff"),
    ("demo.district-admin", "district_admin", "Synthetic District Administrator"),
    ("demo.system-admin", "system_admin", "Synthetic System Administrator"),
)


def _unusable_password_hash() -> str:
    salt = secrets.token_bytes(16)
    random_password = secrets.token_bytes(48)
    digest = hashlib.pbkdf2_hmac("sha256", random_password, salt, 310_000)
    return f"pbkdf2_sha256$310000${salt.hex()}${digest.hex()}"


def seed_data() -> None:
    with SessionLocal.begin() as session:
        existing = session.scalar(select(District.id).where(District.name_en == "Alluri Sitharama Raju"))
        if existing is not None:
            raise RuntimeError("Demo geography already exists. Use reset.py with explicit reset confirmation.")

        district = District(name_en="Alluri Sitharama Raju", name_te="అల్లూరి సీతారామరాజు")
        session.add(district)
        session.flush()

        mandal_rows: list[Mandal] = []
        phc_rows: list[list[PHC]] = []
        village_rows: list[list[Village]] = []
        habitation_rows: list[list[Habitation]] = []

        for mandal_en, mandal_te, _ in MANDALS:
            mandal = Mandal(district_id=district.id, name_en=mandal_en, name_te=mandal_te)
            session.add(mandal)
            session.flush()
            mandal_rows.append(mandal)

            mandal_phcs: list[PHC] = []
            mandal_villages: list[Village] = []
            mandal_habitations: list[Habitation] = []
            for sample_number in (1, 2):
                phc = PHC(
                    mandal_id=mandal.id,
                    name_en=f"{mandal_en} Sample PHC {sample_number}",
                    name_te=f"{mandal_te} నమూనా ప్రాథమిక ఆరోగ్య కేంద్రం {sample_number}",
                    code=f"DEMO-{MANDALS.index((mandal_en, mandal_te, _)) + 1:02d}-{sample_number}",
                )
                gram_panchayat = GramPanchayat(
                    mandal_id=mandal.id,
                    name_en=f"{mandal_en} Sample Gram Panchayat {sample_number}",
                    name_te=f"{mandal_te} నమూనా గ్రామ పంచాయతీ {sample_number}",
                )
                session.add_all((phc, gram_panchayat))
                session.flush()

                village = Village(
                    gram_panchayat_id=gram_panchayat.id,
                    phc_id=phc.id,
                    name_en=f"{mandal_en} Sample Village {sample_number}",
                    name_te=f"{mandal_te} నమూనా గ్రామం {sample_number}",
                )
                session.add(village)
                session.flush()
                habitation = Habitation(
                    village_id=village.id,
                    name_en=f"{mandal_en} Sample Habitation {sample_number}",
                    name_te=f"{mandal_te} నమూనా ఆవాసం {sample_number}",
                )
                session.add(habitation)
                session.flush()
                mandal_phcs.append(phc)
                mandal_villages.append(village)
                mandal_habitations.append(habitation)
            phc_rows.append(mandal_phcs)
            village_rows.append(mandal_villages)
            habitation_rows.append(mandal_habitations)

        users: dict[str, User] = {}
        for username, role, display_name in ROLES:
            suffix = 140 + len(users)
            user = User(
                username=username,
                role=role,
                display_name_ciphertext=encrypt_text(display_name),
                phone_ciphertext=encrypt_text(f"+1-202-555-{suffix:04d}"),
                password_hash=_unusable_password_hash(),
                is_active=False,
                mfa_enabled=role in {"medical_officer", "specialist", "district_admin", "system_admin"},
            )
            session.add(user)
            users[role] = user
        session.flush()

        assignment_scopes = {
            "asha": {"village_id": village_rows[0][0].id},
            "medical_officer": {"phc_id": phc_rows[0][0].id},
            "specialist": {"mandal_id": mandal_rows[0].id},
            "navigator": {"mandal_id": mandal_rows[0].id},
            "hospital_staff": {"phc_id": phc_rows[0][1].id},
            "district_admin": {"district_id": district.id},
            "system_admin": {"district_id": district.id},
        }
        for role, scope in assignment_scopes.items():
            session.add(UserAssignment(user_id=users[role].id, **scope))

        session.add(AIModel(
            name="Aarogya Drishti Synthetic Demo Model",
            version_label="0.1.0-demo",
            is_demo=True,
        ))

        for index in range(40):
            is_hero = index == 0
            mandal_index = 5 if is_hero else index % len(MANDALS)
            mandal_en, _, code = MANDALS[mandal_index]
            patient = Patient(
                patient_token=f"AD-{code}-2026-{index + 1:06d}",
                name_ciphertext=encrypt_text(f"Synthetic Patient {index + 1:02d}"),
                phone_ciphertext=encrypt_text(f"+1-202-555-{100 + index:04d}"),
                age_years=46 if is_hero else 18 + (index * 7) % 70,
                sex="unspecified",
                habitation_id=habitation_rows[mandal_index][index % 2].id,
                is_synthetic=True,
            )
            session.add(patient)
            session.flush()

            household = Household(
                household_code=f"DEMO-HH-{index + 1:04d}",
                habitation_id=patient.habitation_id,
            )
            session.add(household)
            session.flush()
            session.add(HouseholdMember(
                household_id=household.id,
                patient_id=patient.id,
                relation="index",
            ))
            session.add(Consent(
                patient_id=patient.id,
                consent_type="oral_examination",
                status="granted",
                captured_by=users["asha"].id,
                granted_at=datetime.now(timezone.utc),
                evidence={"synthetic_demo": True},
            ))
            case = Case(
                patient_id=patient.id,
                opened_by=users["asha"].id,
                assigned_to=users["medical_officer"].id,
                status="awaiting_review",
                priority_score=None,
                summary_ciphertext=encrypt_text(
                    "Synthetic training scenario; clinician review required."
                    if is_hero else "Synthetic screening record."
                ),
            )
            session.add(case)
            session.flush()
            if is_hero:
                session.add_all((
                    Habit(
                        patient_id=patient.id,
                        habit_type="tobacco_chewing",
                        frequency="synthetic_demo_daily",
                        duration_months=120,
                    ),
                    Symptom(
                        patient_id=patient.id,
                        symptom_type="white_cheek_patch",
                        notes_ciphertext=encrypt_text(
                            "Synthetic example only; needs a doctor's examination."
                        ),
                    ),
                ))

        session.flush()


if __name__ == "__main__":
    seed_data()
    print("Seeded 11 mandals, 22 sample PHCs/villages, 7 inactive role accounts, and 40 synthetic patients.")
