from django.urls import path
from .views import ReceptionistDashboardView, CreatePatientView, GetPatientDetailsView, GetStaffByRoleView, BookAppointmentView, RequestAdmissionView, ListAdmissionRequestsView, ListRecentPatientsView, ListUpcomingAppointmentsView

urlpatterns = [
    path('/dashboard', ReceptionistDashboardView.as_view(), name='receptionist-dashboard'),
    
    path('/patient/register', CreatePatientView.as_view(), name='create-patient'),
    path('/patient/<str:hin>', GetPatientDetailsView.as_view(), name='get-patient-details'),
    path('/patients/recent', ListRecentPatientsView.as_view(), name='recent-patients'),
    
    path('/staff/<str:role>', GetStaffByRoleView.as_view(), name='get-staff-by-role'),
    
    path('/appointments', BookAppointmentView.as_view(), name='book-appointment'),
    path('/appointments/upcoming', ListUpcomingAppointmentsView.as_view(), name='upcoming-appointments'),
    
    path('/admissions/request', RequestAdmissionView.as_view(), name='request-admission'),
    path('/admissions/requests', ListAdmissionRequestsView.as_view(), name='admission-requests'),
]