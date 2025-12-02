import hashlib
from django.utils.timezone import now, timedelta
from .models import NINVerificationAttempt

def hash_nin(nin: str):
    return hashlib.sha256(nin.encode()).hexdigest()
        
def can_attempt_nin_verification(user):
    today = now() - timedelta(hours=24)
    attempts_today = NINVerificationAttempt.objects.filter(user=user, created_at__gte=today).count()
    return attempts_today < 3

def nin_checked_before(user, nin_hash):
    last_success = NINVerificationAttempt.objects.filter(user=user, nin_hash=nin_hash).order_by("-created_at").first()
    if not last_success:
        return False
    
    return True