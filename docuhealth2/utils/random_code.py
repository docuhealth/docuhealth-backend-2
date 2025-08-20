import random

def generate_HIN():
    return ''.join([str(random.randint(0, 9)) for _ in range(13)])

def unique_HIN():
    from core.models import User  
    
    """Generate a HIN that’s unique in the database."""
    while True:
        hin = generate_HIN()
        if not User.objects.filter(hin=hin).exists():
            return hin

def generate_planId():
    return ''.join([str(random.randint(0, 9)) for _ in range(4)])

def get_dh_code(prefix):
    prefix = prefix.upper()
    if len(prefix) != 3 or not prefix.isalpha():
        raise ValueError("Prefix must be exactly 3 alphabetic characters.")
    random_part = ''.join(random.choices('0123456789', k=10))
    return f"{prefix}-{random_part}"

