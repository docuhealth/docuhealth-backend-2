from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser

from .models import MedicalRecord, MedicalRecordAttachment
from .serializers import MedicalRecordSerializer, MedicalRecordAttachmentSerializer

class MedicalRecordListView(generics.ListAPIView):
    queryset = MedicalRecord.objects.all().order_by('-created_at')
    serializer_class = MedicalRecordSerializer

class MedicalRecordCreateView(generics.CreateAPIView):
    queryset = MedicalRecord.objects.all()
    serializer_class = MedicalRecordSerializer
    
    def perform_create(self, serializer):
        serializer.save(hospital=self.request.user)
        
class ListUserMedicalrecordsView(generics.ListAPIView):
    serializer_class = MedicalRecordSerializer
    
    def get_queryset(self):
        user = self.request.user
        role = user.role
        
        if role == 'patient':
            return MedicalRecord.objects.filter(patient=user).select_related("patient", "hospital").prefetch_related("drug_records", "attachments").order_by('-created_at')
        
        if role == 'hospital':
            return MedicalRecord.objects.filter(hospital=user).select_related("patient", "hospital").prefetch_related("drug_records", "attachments").order_by('-created_at')
        
class UploadMedicalRecordsAttachments(generics.CreateAPIView):
    queryset = MedicalRecordAttachment.objects.all()
    serializer_class = MedicalRecordAttachmentSerializer
    parser_classes = [MultiPartParser, FormParser]
    
    def create(self, request, *args, **kwargs):
        files = request.FILES.getlist("files")  
        attachments = []

        for file in files:
            serializer = self.get_serializer(data={"file": file})
            serializer.is_valid(raise_exception=True)
            attachment = serializer.save()
            attachments.append(serializer.data)
            
        attachment_ids = [attachment['id'] for attachment in attachments]
        return Response(attachment_ids, status=status.HTTP_201_CREATED)
        
