from django.urls import path

from accounts.views import LoginView, CustomTokenRefreshView, ForgotPassword, VerifyForgotPasswordOTPView, ResetPasswordView, ListUserView, VerifySignupOTPView, UpdatePasswordView, VerifyUserNINView, DoctorDashboardView, TeamMemberCreateView, TeamMemberListView, RemoveTeamMembersView, TeamMemberUpdateRoleView, PatientDashboardView, CreatePatientView, UpdatePatientView, DeletePatientAccountView, ListCreateSubaccountView, UpgradeSubaccountView, ToggleEmergencyView, GeneratePatientIdCard, GenerateSubaccountIdCard, NurseDashboardView, ReceptionistDashboardView, GetPatientDetailsView, GetStaffByRoleView

from records.views import CreateMedicalRecordView, MedicalRecordListView, UploadMedicalRecordsAttachments, ListUserMedicalrecordsView, RequestVitalSignsView, RetrievePatientInfoView, ListPatientMedicalRecordsView, RequestAdmissionView, ConfirmAdmissionView, ListAdmittedPatientsByStatusView, ListSubaccountMedicalRecordsView, ListAdmissionsView, ListAdmissionRequestsView, ListVitalSignsRequest, ProcessVitalSignsRequestView, UpdatePatientVitalSignsView, CreateCaseNotesView, ListCaseNotesView

from hospital_ops.views import ListAllAppointmentsView, ListStaffAppointmentsView, AssignAppointmentToDoctorView, HandOverNurseShiftView, ListPatientAppointmentsView, BookAppointmentView, ListUpcomingAppointmentsView, ListRecentPatientsView

from organizations.views import CreateHospitalView, ListHospitalsView, ListCreateHospitalInquiryView, ListCreateHospitalVerificationRequestView, ApproveVerificationRequestView,  GetHospitalInfo, ListCreateSubscriptionPlanView, CreateSubscriptionView

from organizations.webhooks import PaystackWebhookView

from facility.views import ListCreateWardsView, RetrieveUpdateDeleteWardView, ListBedsByWardView

auth_urls = [
     path('signup/verify-otp', VerifySignupOTPView.as_view(), name='verify-signup-otp'),
    path('login', LoginView.as_view(), name='user-login'),
    path('refresh', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('forgot-password', ForgotPassword.as_view(), name='forgot-password'),
    path('forgot-password/verify-otp', VerifyForgotPasswordOTPView.as_view(), name='verify-otp'),
    path('reset-password', ResetPasswordView.as_view(), name='reset-password'),
    path('users/all', ListUserView.as_view(), name='users'),
    
    path('nin', VerifyUserNINView.as_view(), name='verify-user-nin'),
    path('hospital-staff/password', UpdatePasswordView.as_view(), name="update-hospital-staff-password")
]

medical_records_urls = [
    path('', CreateMedicalRecordView.as_view(), name='create-medical-records'),
    path('/upload-attachments', UploadMedicalRecordsAttachments.as_view(), name='medical-records-attachments'),
    path('/user-records', ListUserMedicalrecordsView.as_view(), name='patient-medical-records'),
    path('/all', MedicalRecordListView.as_view(), name='get-medical-records'),
]

doctor_urls = [
    path('/dashboard', DoctorDashboardView.as_view(), name='doctor-dashboard'),
    
    path('/vital-signs/request', RequestVitalSignsView.as_view(), name='request-vital-signs'),
    path('/appointments', ListStaffAppointmentsView.as_view(), name='appointments'),
    
    path('/patient/info/<int:hin>', RetrievePatientInfoView.as_view(), name='retrieve-patient-info'),
    path('/patient/records/<int:hin>', ListPatientMedicalRecordsView.as_view(), name='list-patient-medical-records'),
    
    path('/admissions/request', RequestAdmissionView.as_view(), name='request-admission'),
    path('/admissions/<str:admission_id>/confirm', ConfirmAdmissionView.as_view(), name='admission-requests'),
]

hospital_urls = [
    path('', CreateHospitalView.as_view(), name='create-hospital'),
    path('/hospitals', ListHospitalsView.as_view(), name='list-hospitals'),
    
    path('/inquiries', ListCreateHospitalInquiryView.as_view(), name='create-inquiry'),
    path('/verification-request', ListCreateHospitalVerificationRequestView.as_view(), name='list-create-verification-request'),
    path('/approve-verification', ApproveVerificationRequestView.as_view(), name='approve-verification-request'),
    
    path('/team-member', TeamMemberCreateView.as_view(), name='create-team-member'),
    path('/team-members', TeamMemberListView.as_view(), name='list-team-member'),
    path('/team-members/remove', RemoveTeamMembersView.as_view(), name='remove-team-member'),
    path('/team-member/<str:staff_id>/update-role', TeamMemberUpdateRoleView.as_view(), name='update-team-member-role'),
    
    path('/appointments', ListAllAppointmentsView.as_view(), name='get-appointments'),
    path('/info', GetHospitalInfo.as_view(), name='get-hospital-info'),
    
    path('/wards', ListCreateWardsView.as_view(), name='list-create-wards'),
    path('/wards/<str:ward_id>', RetrieveUpdateDeleteWardView.as_view(), name='retrieve-update-delete-ward'),
    path('/wards/<str:ward_id>/beds', ListBedsByWardView.as_view(), name='list-beds-by-ward'),
    
    path('/admissions/<str:status>', ListAdmittedPatientsByStatusView.as_view(), name='list-admitted-patients-by-status'),
    path('/admissions/<str:admission_id>/confirm', ConfirmAdmissionView.as_view(), name='admission-requests'),

]

nurse_urls = [
    path('/dashboard', NurseDashboardView.as_view(), name='nurse-dashboard'),
    
    path('/admissions', ListAdmissionsView.as_view(), name='admissions'),
    path('/admissions/requests', ListAdmissionRequestsView.as_view(), name='admission-requests'),
    
    path('/vital-signs/requests', ListVitalSignsRequest.as_view(), name='list-vital-signs-requests'),
    path('/vital-signs/process', ProcessVitalSignsRequestView.as_view(), name='process-vital-signs-requests'),
    path('/vital-signs/update', UpdatePatientVitalSignsView.as_view(), name='update-patient-vital-signs'),
    
    path('/appointments', ListStaffAppointmentsView.as_view(), name='get-appointments'),
    path('/appointments/<int:pk>/assign', AssignAppointmentToDoctorView.as_view(), name='assign-appointment'),
    
    path('/handover', HandOverNurseShiftView.as_view(), name='handover-nurse-shift'),
    
    path('/case-notes', CreateCaseNotesView.as_view(), name='create-case-notes'),
    path('/case-notes/patient/<int:hin>', ListCaseNotesView.as_view(), name='list-case-notes-by-patient'),
    # path('/case-notes/<int:pk>', RetrieveCaseNoteView.as_view(), name='retrieve-case-note'),   
]

patient_urls = [
     path('', CreatePatientView.as_view(), name='create-patient'),
    path('/dashboard', PatientDashboardView.as_view(), name='patient-dashboard'),
    path('/update', UpdatePatientView.as_view(), name='update-patient'),
    path('/delete', DeletePatientAccountView.as_view(), name='delete-patient'),
    path('/subaccounts', ListCreateSubaccountView.as_view(), name='create-subaccount'),
    path('/subaccounts/medical-records/<int:hin>', ListSubaccountMedicalRecordsView.as_view(), name='get-subaccount-medical-records'),
    path('/subaccounts/upgrade', UpgradeSubaccountView.as_view(), name='upgrade-subaccount'),
    path('/appointments', ListPatientAppointmentsView.as_view(), name='get-appointments'),
    path('/emergency', ToggleEmergencyView.as_view(), name='toggle-emergency'),
    path('/id-card', GeneratePatientIdCard.as_view(), name='generate-patient-id-card'),
    path('/subaccounts/id-card/<int:hin>', GenerateSubaccountIdCard.as_view(), name='generate-subaccount-id-card'),
]

receptionist_urls = [
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

subscription_urls = [
    path('/plans', ListCreateSubscriptionPlanView.as_view(), name='create-subscription-plan'),
    path('/subscribe', CreateSubscriptionView.as_view(), name='subscribe to plan'),
    path('/paystack_webhook', PaystackWebhookView.as_view(), name='paystack-webhook'),
]
