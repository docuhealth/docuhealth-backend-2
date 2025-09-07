from django.urls import path
from .views import MedicalRecordCreateView, MedicalRecordListView, UploadMedicalRecordsAttachments

urlpatterns = [
    path('', MedicalRecordListView.as_view(), name='medical-records'),
    path('create', MedicalRecordCreateView.as_view(), name='create-medical-records'),
    path('upload', UploadMedicalRecordsAttachments.as_view(), name='medical-records-attachments'),
]