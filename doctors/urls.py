from django.urls import path
from .views import RequestVitalSignsView, ListAppointmentsView, RetrievePatientInfoView, ListPatientMedicalRecordsView, ConfirmAdmissionView, RequestAdmissionView, DoctorDashboardView

urlpatterns = [
    path('/dashboard', DoctorDashboardView.as_view(), name='doctor-dashboard'),
    
    path('/vital-signs/request', RequestVitalSignsView.as_view(), name='request-vital-signs'),
    path('/appointments', ListAppointmentsView.as_view(), name='appointments'),
    
    path('/patient/info/<int:hin>', RetrievePatientInfoView.as_view(), name='retrieve-patient-info'),
    path('/patient/records/<int:hin>', ListPatientMedicalRecordsView.as_view(), name='list-patient-medical-records'),
    
    path('/admissions/request', RequestAdmissionView.as_view(), name='request-admission'),
    path('/admissions/<str:admission_id>/confirm', ConfirmAdmissionView.as_view(), name='admission-requests'),
]