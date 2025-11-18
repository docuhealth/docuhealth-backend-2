from django.urls import path
from .views import ReceptionistDashboardView, CreatePatientView, GetPatientDetailsView, GetStaffByRoleView

urlpatterns = [
    path('/dashboard', ReceptionistDashboardView.as_view(), name='receptionist-dashboard'),
    path('/register-patient', CreatePatientView.as_view(), name='create-patient'),
    path('/patient/<str:hin>', GetPatientDetailsView.as_view(), name='get-patient-details'),
    path('/staff/<str:role>', GetStaffByRoleView.as_view(), name='get-staff-by-role'),
]