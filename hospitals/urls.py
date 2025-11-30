from django.urls import path
from .views import CreateHospitalView, ListCreateHospitalInquiryView, ListCreateHospitalVerificationRequestView, ApproveVerificationRequestView, TeamMemberCreateView, TeamMemberListView, RemoveTeamMembersView, TeamMemberUpdateRoleView, ListAppointmentsView, GetHospitalInfo, ListCreateWardsView, RetrieveUpdateDeleteWardView, ListBedsByWardView, ListAdmittedPatientsByStatusView, ConfirmAdmissionView, ListHospitalsView

urlpatterns = [
    path('', CreateHospitalView.as_view(), name='create-hospital'),
    path('/hospitals', ListHospitalsView.as_view(), name='list-hospitals'),
    
    path('/inquiries', ListCreateHospitalInquiryView.as_view(), name='create-inquiry'),
    path('/verification-request', ListCreateHospitalVerificationRequestView.as_view(), name='list-create-verification-request'),
    path('/approve-verification', ApproveVerificationRequestView.as_view(), name='approve-verification-request'),
    
    path('/team-member', TeamMemberCreateView.as_view(), name='create-team-member'),
    path('/team-members', TeamMemberListView.as_view(), name='list-team-member'),
    path('/team-members/remove', RemoveTeamMembersView.as_view(), name='remove-team-member'),
    path('/team-member/<str:staff_id>/update-role', TeamMemberUpdateRoleView.as_view(), name='update-team-member-role'),
    
    path('/appointments', ListAppointmentsView.as_view(), name='get-appointments'),
    path('/info', GetHospitalInfo.as_view(), name='get-hospital-info'),
    
    path('/wards', ListCreateWardsView.as_view(), name='list-create-wards'),
    path('/wards/<str:ward_id>', RetrieveUpdateDeleteWardView.as_view(), name='retrieve-update-delete-ward'),
    path('/wards/<str:ward_id>/beds', ListBedsByWardView.as_view(), name='list-beds-by-ward'),
    
    path('/admissions/<str:status>', ListAdmittedPatientsByStatusView.as_view(), name='list-admitted-patients-by-status'),
    path('/admissions/<str:admission_id>/confirm', ConfirmAdmissionView.as_view(), name='admission-requests'),

]