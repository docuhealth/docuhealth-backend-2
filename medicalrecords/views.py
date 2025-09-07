from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status

from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .parsers import MultipartJsonParser

from .models import MedicalRecord, MedicalRecordAttachment
from .serializers import MedicalRecordSerializer, MedicalRecordAttachmentSerializer

class MedicalRecordListView(generics.ListAPIView):
    queryset = MedicalRecord.objects.all()
    serializer_class = MedicalRecordSerializer

class MedicalRecordCreateView(generics.ListCreateAPIView):
    queryset = MedicalRecord.objects.all()
    serializer_class = MedicalRecordSerializer
    
    def perform_create(self, serializer):
        serializer.save(hospital=self.request.user)
        
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
        
