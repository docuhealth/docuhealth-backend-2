from django.urls import path
from .views import NurseDashboardView, ListAdmissionRequestsView, ListVitalSignsRequest, ProcessVitalSignsRequestView, ListAppointmentsView, AssignAppointmentToDoctorView, ListAdmissionsView, UpdatePatientVitalSignsView

urlpatterns = [
    path('/dashboard', NurseDashboardView.as_view(), name='nurse-dashboard'),
    
    path('/admissions', ListAdmissionsView.as_view(), name='admissions'),
    path('/admissions/requests', ListAdmissionRequestsView.as_view(), name='admission-requests'),
    
    path('/vital-signs/requests', ListVitalSignsRequest.as_view(), name='list-vital-signs-requests'),
    path('/vital-signs/process', ProcessVitalSignsRequestView.as_view(), name='process-vital-signs-requests'),
    path('/vital-signs/update', UpdatePatientVitalSignsView.as_view(), name='update-patient-vital-signs'),
    
    path('/appointments', ListAppointmentsView.as_view(), name='get-appointments'),
    path('/appointments/<int:pk>/assign', AssignAppointmentToDoctorView.as_view(), name='assign-appointment'),
    
]