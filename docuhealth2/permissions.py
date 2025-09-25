from rest_framework.permissions import BasePermission
from core.models import User

class BaseRolePermission(BasePermission):
    role = None
    require_auth = True  

    def has_permission(self, request, view):
        if self.require_auth and not request.user.is_authenticated:
            return False
        return (
            self.role is not None
            and getattr(request.user, "role", None) == self.role
        )
        
class IsPatient(BaseRolePermission):
    role = User.Role.PATIENT
    require_auth = False  

class IsAuthenticatedPatient(BaseRolePermission):
    role = User.Role.PATIENT
    
class IsHospital(BaseRolePermission):
    role = User.Role.HOSPITAL
    require_auth = False
    
class IsAuthenticatedHospital(BaseRolePermission):
    role = User.Role.HOSPITAL
    
class IsAdmin(BaseRolePermission):
    role = User.Role.ADMIN
    require_auth = False
    
class IsAuthenticatedAdmin(BaseRolePermission):
    role = User.Role.ADMIN