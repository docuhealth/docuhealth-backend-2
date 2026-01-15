from django.urls import path

from .views import CreatePharmacyOnboardingRequest, ListPharmacyOnboardingRequest, RetrievePharmacyOnboardingRequest, ApprovePharmacyOnboardingRequestView, PharmacyRotateKeyView

from records.views import PharmacyDrugRecordUploadView

pharmacy_urls = [
    path('', CreatePharmacyOnboardingRequest.as_view(), name='create-pharmacy-onboarding-request'),
    path('/requests', ListPharmacyOnboardingRequest.as_view(), name='list-pharmacy-onboarding-request'),
    path('/requests/<str:id>', RetrievePharmacyOnboardingRequest.as_view(), name='retrieve-pharmacy-onboarding-request'),
    path('/request/approve', ApprovePharmacyOnboardingRequestView.as_view(), name='approve-pharmacy-onboarding-request'),

    path('/drug-records/upload', PharmacyDrugRecordUploadView.as_view(), name='pharmacy-drug-records-upload'),
    path('/rotate-key', PharmacyRotateKeyView.as_view(), name='pharmacy-rotate-key'),
]

