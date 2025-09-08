from django.urls import path
from .views import MedicalRecordCreateView, MedicalRecordListView, UploadMedicalRecordsAttachments, ListUserMedicalrecordsView

urlpatterns = [
    path('create', MedicalRecordCreateView.as_view(), name='create-medical-records'),
    path('upload-attachments', UploadMedicalRecordsAttachments.as_view(), name='medical-records-attachments'),
    path('user-records', ListUserMedicalrecordsView.as_view(), name='patient-medical-records'),
    path('all', MedicalRecordListView.as_view(), name='get-medical-records'),
]