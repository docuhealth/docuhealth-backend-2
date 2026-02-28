from django.urls import path

from accounts.views import DeactivateTeamMembersView, LoginView, CustomTokenRefreshView, ForgotPassword, VerifyForgotPasswordOTPView, ResetPasswordView, ListUserView, VerifySignupOTPView, UpdatePasswordView, VerifyUserNINView, DoctorDashboardView, TeamMemberCreateView, TeamMemberListView, RemoveTeamMembersView, TeamMemberUpdateRoleView, PatientDashboardView, CreatePatientView, UpdatePatientView, DeletePatientAccountView, ListCreateSubaccountView, UpgradeSubaccountView, ToggleEmergencyView, GeneratePatientIdCard, GenerateSubaccountIdCard, NurseDashboardView, ReceptionistDashboardView, GetPatientDetailsView, GetStaffByRoleView, ReceptionistCreatePatientView, SendEmailOTPView, VerifyEmailOTPView, UpdateProfileView, UpdateHospitalAdminProfileView

from records.views import MedicalRecordListView, ListUserMedicalrecordsView, RequestVitalSignsView, RetrievePatientInfoView, ListPatientMedicalRecordsView, RequestAdmissionView, ConfirmAdmissionView, ListAdmittedPatientsByStatusView, ListSubaccountMedicalRecordsView, ListAdmissionsView, ListAdmissionRequestsView, ListVitalSignsRequest, ProcessVitalSignsRequestView, UpdatePatientVitalSignsView, CreateCaseNotesView, ListCaseNotesView, ListPatientDrugRecordsView, CreateSoapNoteView, ListPatientSoapNotesView, DischargePatientView, ListPatientDischargeFormsView, CreateSoapNoteAdditionalNotesView

from hospital_ops.views import ListAllAppointmentsView, ListStaffAppointmentsView, AssignAppointmentToDoctorView, HandOverNurseShiftView, ListPatientAppointmentsView, BookAppointmentView, ListUpcomingAppointmentsView, ListRecentPatientsView, TransferPatientToWardView

from organizations.views import CreateHospitalView, ListHospitalsView, ListCreateHospitalInquiryView, ListCreateHospitalVerificationRequestView, ApproveVerificationRequestView,  GetHospitalInfo, ListCreateSubscriptionPlanView, CreateSubscriptionView, ListSubscriptionPlansByRoleView

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
    path('hospital/password', UpdatePasswordView.as_view(), name="update-hospital-staff-password"),
    
    path('email/send-otp', SendEmailOTPView.as_view(), name='send-email-otp'),
    path('email/verify-otp', VerifyEmailOTPView.as_view(), name='verify-email-otp'),
    
    path('profile', UpdateProfileView.as_view(), name='update-profile'),
    path('hospital-admin-profile', UpdateHospitalAdminProfileView.as_view(), name='update-hospital-admin-profile'),
]

medical_records_urls = [
    path('/user-records', ListUserMedicalrecordsView.as_view(), name='patient-medical-records'),
    path('/all', MedicalRecordListView.as_view(), name='get-medical-records'),
    
    path('/discharge', DischargePatientView.as_view(), name='discharge-patient'),
    path('/discharge-form/<str:hin>', ListPatientDischargeFormsView.as_view(), name='list-patient-discharge-forms'),
    path('/soap-note/additional-notes', CreateSoapNoteAdditionalNotesView.as_view(), name='create-soap-note-additional-notes'),
    
    path('/soap-note/<str:hin>', ListPatientSoapNotesView.as_view(), name='list-patient-soap-notes'),
    path('/soap-note', CreateSoapNoteView.as_view(), name='create-soap-note'),
]

doctor_urls = [
    path('/dashboard', DoctorDashboardView.as_view(), name='doctor-dashboard'),
    
    path('/vital-signs/request', RequestVitalSignsView.as_view(), name='request-vital-signs'),
    path('/appointments', ListStaffAppointmentsView.as_view(), name='appointments'),
    
    path('/patient/info/<str:hin>', RetrievePatientInfoView.as_view(), name='retrieve-patient-info'),
    path('/patient/records/<str:hin>', ListPatientMedicalRecordsView.as_view(), name='list-patient-medical-records'),
    
    path('/admissions/request', RequestAdmissionView.as_view(), name='request-admission'),
    path('/admissions/<str:admission_id>/confirm', ConfirmAdmissionView.as_view(), name='admission-requests'),
    
    path('/admissions/transfer', TransferPatientToWardView.as_view(), name='transfer-patient-to-ward'),
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
    path('/team-members/deactivate', DeactivateTeamMembersView.as_view(), name='deactivate-team-member'),
    path('/team-member/<str:staff_id>/update-role', TeamMemberUpdateRoleView.as_view(), name='update-team-member-role'),
    
    path('/appointments', ListAllAppointmentsView.as_view(), name='get-appointments'),
    path('/info', GetHospitalInfo.as_view(), name='get-hospital-info'),
    
    path('/wards', ListCreateWardsView.as_view(), name='list-create-wards'),
    path('/wards/<str:ward_id>', RetrieveUpdateDeleteWardView.as_view(), name='retrieve-update-delete-ward'),
    path('/wards/<str:ward_id>/beds', ListBedsByWardView.as_view(), name='list-beds-by-ward'),
    
    path('/admissions/<str:status>', ListAdmittedPatientsByStatusView.as_view(), name='list-admitted-patients-by-status'),
    path('/admissions/<str:admission_id>/confirm', ConfirmAdmissionView.as_view(), name='confirm-admission-requests'),
    
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
    path('/case-notes/patient/<str:hin>', ListCaseNotesView.as_view(), name='list-case-notes-by-patient'),
    # path('/case-notes/<int:pk>', RetrieveCaseNoteView.as_view(), name='retrieve-case-note'),   
]

patient_urls = [
    path('', CreatePatientView.as_view(), name='create-patient'),
    path('/dashboard', PatientDashboardView.as_view(), name='patient-dashboard'),
    path('/update', UpdatePatientView.as_view(), name='update-patient'),
    path('/delete', DeletePatientAccountView.as_view(), name='delete-patient'),
    path('/subaccounts', ListCreateSubaccountView.as_view(), name='create-subaccount'),
    path('/subaccounts/medical-records/<str:hin>', ListSubaccountMedicalRecordsView.as_view(), name='get-subaccount-medical-records'),
    path('/subaccounts/upgrade', UpgradeSubaccountView.as_view(), name='upgrade-subaccount'),
    path('/appointments', ListPatientAppointmentsView.as_view(), name='get-appointments'),
    path('/drug-records', ListPatientDrugRecordsView.as_view(), name='get-drug-records'),
    path('/emergency', ToggleEmergencyView.as_view(), name='toggle-emergency'),
    path('/id-card', GeneratePatientIdCard.as_view(), name='generate-patient-id-card'),
    path('/subaccounts/id-card/<str:hin>', GenerateSubaccountIdCard.as_view(), name='generate-subaccount-id-card'),
]

receptionist_urls = [
    path('/dashboard', ReceptionistDashboardView.as_view(), name='receptionist-dashboard'),
    
    path('/patient/register', ReceptionistCreatePatientView.as_view(), name='create-patient'),
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
    path('/plans/<str:role>', ListSubscriptionPlansByRoleView.as_view(), name='list-subscription-plans-by-role'),
]
