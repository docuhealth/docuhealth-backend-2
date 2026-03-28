import random
from django.db.models import Max
import re
from django.db import connection
from django.db import transaction
from django.db.models import F

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

def get_next_staff_seq(hospital_instance, prefix: str) -> int:
    """
    Fetches the next value from a PostgreSQL sequence specific to the hospital.
    Creates the sequence if it does not already exist.
    """
    seq_name = f"staff_id_seq_hosp_{hospital_instance.id}"
    
    with connection.cursor() as cursor:
        cursor.execute(f"CREATE SEQUENCE IF NOT EXISTS {seq_name} START 1;")
        
        cursor.execute(f"SELECT last_value, is_called FROM pg_sequences WHERE schemaname = 'public' AND sequencename = '{seq_name}';")
        seq_status = cursor.fetchone()
        
        if seq_status and not seq_status[1]: 
            from accounts.models import HospitalStaffProfile
            
            latest_id = HospitalStaffProfile.objects.filter(
                hospital=hospital_instance, 
                staff_id__startswith=prefix
            ).aggregate(max_val=Max("staff_id")).get("max_val")

            if latest_id:
                match = re.search(r'(\d+)$', latest_id)
                current_max = int(match.group(1)) if match else 0
                
                if current_max > 0:
                    cursor.execute(f"SELECT setval('{seq_name}', {current_max});")

        cursor.execute(f"SELECT nextval('{seq_name}');")
        return cursor.fetchone()[0]

def generate_staff_id(hospital_instance, role: str = "default") -> str:
    """
    Generates a unique, human-readable staff ID.
    Format: <HOSP_ABBR>-<ROLE_ABBR><SEQUENCE>
    Example: OLVC-DR001
    """
    from accounts.models import HospitalStaffProfile 

    clean_name = ''.join(ch for ch in hospital_instance.name.upper() if ch.isalpha())
    hosp_abbr = (clean_name[:4] if len(clean_name) >= 4 else clean_name).ljust(4, 'X')

    role_prefix = ROLE_PREFIX_MAP.get(role, ROLE_PREFIX_MAP["default"])
    
    # 2. Get the Atomic Sequence Number from DB
    new_seq_int = get_next_staff_seq(hospital_instance, role_prefix)
    new_seq_str = str(new_seq_int).zfill(3)

    return f"{hosp_abbr}-{role_prefix}{new_seq_str}"

def get_next_staff_id(hospital, role):
    clean_name = ''.join(ch for ch in hospital.name.upper() if ch.isalpha())
    hosp_abbr = (clean_name[:4] if len(clean_name) >= 4 else clean_name).ljust(4, 'X')
    
    role_prefix = ROLE_PREFIX_MAP.get(role, ROLE_PREFIX_MAP["default"])
    
    from accounts.models import StaffCounter
    
    with transaction.atomic():
        counter, _ = StaffCounter.objects.select_for_update().get_or_create(
            hospital=hospital,
            role=role,
            defaults={"current_value": 0}
        )

        counter.current_value = F("current_value") + 1
        counter.save()
        counter.refresh_from_db()

        return f"{hosp_abbr}-{role_prefix}{str(counter.current_value).zfill(3)}"

