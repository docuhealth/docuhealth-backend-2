import random

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

