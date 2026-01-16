from rest_framework.permissions import BasePermission
from accounts.models import User, HospitalStaffProfile
from organizations.models import Client

class BaseRolePermission(BasePermission):
    role = None
    require_auth = True  

    def has_permission(self, request, view):
        if not request.user:
            return False
        
        if self.require_auth and not request.user.is_authenticated:
            return False
        
        return (
            self.role is not None
            and str(getattr(request.user, "role", None)) == str(self.role)
        )
        
class StaffRolePermission(BasePermission):
    required_staff_role = None
    require_auth = True

    def has_permission(self, request, view):
        if self.require_auth and not request.user.is_authenticated:
            return False
        
        if request.user.role != User.Role.HOSPITAL_STAFF:
            return False
        
        staff_profile = getattr(request.user, "hospital_staff_profile", None)
        if not staff_profile:
            return False
        
        return staff_profile.role == self.required_staff_role
    
class StaffSameHospitalPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        staff_profile = getattr(request.user, "hospital_staff_profile", None)
        if not staff_profile:
            return False
        
        # Every object we protect **must have a .hospital field**
        obj_hospital = getattr(obj, "hospital", None)
        if obj_hospital is None:
            return False
        
        return obj_hospital == staff_profile.hospital
        
class IsPatient(BaseRolePermission):
    role = User.Role.PATIENT
    require_auth = False  

class IsAuthenticatedPatient(BaseRolePermission):
    role = User.Role.PATIENT
    
class IsDHAdmin(BaseRolePermission):
    role = User.Role.DHADMIN
    require_auth = False
    
class IsAuthenticatedDHAdmin(BaseRolePermission):
    role = User.Role.DHADMIN
    
class IsAuthenticatedPharmacy(BaseRolePermission):
    role = User.Role.PHARMACY
    
class IsAuthenticatedPharmacyPartner(BaseRolePermission):
    role = User.Role.PHARMACY_PARTNER
    
class IsHospitalAdmin(BaseRolePermission):
    role = User.Role.HOSPITAL
    require_auth = False
    
class IsAuthenticatedHospitalAdmin(BaseRolePermission):
    role = User.Role.HOSPITAL
    
class IsHospitalStaff(BaseRolePermission):
    role = User.Role.HOSPITAL_STAFF
    require_auth = False
    
class IsAuthenticatedHospitalStaff(BaseRolePermission):
    role = User.Role.HOSPITAL_STAFF
    
class IsAuthenticatedDoctor(StaffRolePermission):
    required_staff_role = HospitalStaffProfile.StaffRole.DOCTOR

class IsAuthenticatedNurse(StaffRolePermission):
    required_staff_role = HospitalStaffProfile.StaffRole.NURSE
    
class IsAuthenticatedReceptionist(StaffRolePermission):
    required_staff_role = HospitalStaffProfile.StaffRole.RECEPTIONIST
    
class IsAuthenticatedPharmacyClient(BasePermission):
    def has_permission(self, request, view):
        return isinstance(request.auth, Client)