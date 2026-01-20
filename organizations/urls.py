from django.urls import path

from .views import CreatePharmacyPartnerView, CreatePharmacyOnboardingRequest, PharmacyPartnerRotateKeyView, ListPharmacyOnboardingView, ApprovePharmacyOnboardingRequestView, RotatePharmacyCodeView, GetPharmacyPartnerClientInfo

from records.views import PharmacyDrugRecordUploadView

pharmacy_urls = [
    path('/request', CreatePharmacyOnboardingRequest.as_view(), name='create-pharmacy-onboarding-request'),
    path('/requests', ListPharmacyOnboardingView.as_view(), name='list-pharmacy-onboarding-request'),
    path('/drug-records/upload', PharmacyDrugRecordUploadView.as_view(), name='pharmacy-drug-records-upload'),
    path('/rotate-key', PharmacyPartnerRotateKeyView.as_view(), name='partner-rotate-key'),
]

partner_urls = [
    # path('/requests/<str:id>', RetrievePharmacyOnboardingRequest.as_view(), name='retrieve-pharmacy-onboarding-request'),
    path('/rotate-code', RotatePharmacyCodeView.as_view(), name='rotate-pharmacy-code'),
    path('/request/approve', ApprovePharmacyOnboardingRequestView.as_view(), name='approve-pharmacy-onboarding-request'),
    path('/info', GetPharmacyPartnerClientInfo.as_view(), name="get-partner-client-info"),
    
    path('/partner', CreatePharmacyPartnerView.as_view(), name='create-pharmacy-partner'),
]

