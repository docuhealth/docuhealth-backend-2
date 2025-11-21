from django.urls import path
from .views import ReceptionistDashboardView, CreatePatientView, GetPatientDetailsView, GetStaffByRoleView, BookAppointmentView, RequestAdmissionView, ListAdmissionRequestsView

urlpatterns = [
    path('/dashboard', ReceptionistDashboardView.as_view(), name='receptionist-dashboard'),
    path('/register-patient', CreatePatientView.as_view(), name='create-patient'),
    path('/patient/<str:hin>', GetPatientDetailsView.as_view(), name='get-patient-details'),
    path('/staff/<str:role>', GetStaffByRoleView.as_view(), name='get-staff-by-role'),
    path('/appointments', BookAppointmentView.as_view(), name='book-appointment'),
    path('/admissions/request', RequestAdmissionView.as_view(), name='request-admission'),
    path('/admissions/requests', ListAdmissionRequestsView.as_view(), name='admission-requests'),
    # path('/password', UpdatePasswordView.as_view(), name="update-password")
]