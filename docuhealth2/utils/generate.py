import random
import string
from django.db.models import Max

def generate_HIN():
    return ''.join([str(random.randint(0, 9)) for _ in range(13)])

def generate_planId():
    return ''.join([str(random.randint(0, 9)) for _ in range(4)])

def get_dh_code(prefix):
    prefix = prefix.upper()
    if len(prefix) != 3 or not prefix.isalpha():
        raise ValueError("Prefix must be exactly 3 alphabetic characters.")
    random_part = ''.join(random.choices('0123456789', k=10))
    return f"{prefix}-{random_part}"

def generate_otp():
    return str(random.randint(100000, 999999))

ROLE_PREFIX_MAP = {
    "doctor": "DR",
    "nurse": "NR",
    "receptionist": "RC",
    "lab_tech": "LB",
    "pharmacist": "PH",
    "default": "STF",  # fallback
}

def generate_staff_id(hospital_name: str, role: str = "default") -> str:
    """
    Generates a unique, human-readable staff ID.
    Format: <HOSP_ABBR>-<ROLE_ABBR><SEQUENCE>
    Example: OLVC-DR001
    """
    from accounts.models import HospitalStaffProfile 

    # Create a short hospital abbreviation (4 chars max)
    clean_name = ''.join(ch for ch in hospital_name.upper() if ch.isalpha())
    hosp_abbr = (clean_name[:4] if len(clean_name) >= 4 else clean_name).ljust(4, 'X')

    role_prefix = ROLE_PREFIX_MAP.get(role, ROLE_PREFIX_MAP["default"])

    # Find the current max sequence number for this hospital and role
    latest_id = (
        HospitalStaffProfile.objects
        .filter(staff_id__startswith=f"{hosp_abbr}-{role_prefix}")
        .aggregate(Max("staff_id"))
    )

    # Extract last sequence (if any)
    last_staff_id = latest_id.get("staff_id__max")
    if last_staff_id:
        try:
            last_seq = int(last_staff_id[-3:])
        except ValueError:
            last_seq = 0
    else:
        last_seq = 0

    # Increment and pad
    new_seq = str(last_seq + 1).zfill(3)

    return f"{hosp_abbr}-{role_prefix}{new_seq}"

