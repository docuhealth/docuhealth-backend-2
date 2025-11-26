from django.urls import path
from .views import NurseDashboardView, ListAdmissionRequestsView, ConfirmAdmissionView, ListVitalSignsRequest, ProcessVitalSignsRequestView, ListAppointmentsView, AssignAppointmentToDoctorView, ListAdmissionsView

urlpatterns = [
    path('/dashboard', NurseDashboardView.as_view(), name='nurse-dashboard'),
    
    path('/admissions', ListAdmissionsView.as_view(), name='admissions'),
    path('/admissions/requests', ListAdmissionRequestsView.as_view(), name='admission-requests'),
    path('/admissions/<str:admission_id>/confirm', ConfirmAdmissionView.as_view(), name='admission-requests'),
    
    path('/vital-signs/requests', ListVitalSignsRequest.as_view(), name='list-vital-signs-requests'),
    path('/vital-signs/process', ProcessVitalSignsRequestView.as_view(), name='process-vital-signs-requests'),
    
    path('/appointments', ListAppointmentsView.as_view(), name='get-appointments'),
    path('/appointments/<int:pk>/assign', AssignAppointmentToDoctorView.as_view(), name='assign-appointment'),
    
]