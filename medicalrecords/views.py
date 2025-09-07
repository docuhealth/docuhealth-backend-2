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
    
    def post(self, request, *args, **kwargs):
        attachments = request.FILES.getlist('attachments', [])
        data = request.data
        print(data)
        return super().post(request, *args, **kwargs, attachments=attachments)

    def perform_create(self, serializer):
        serializer.save(hospital=self.request.user)
        
class UploadMedicalRecordsAttachments(generics.CreateAPIView):
    queryset = MedicalRecordAttachment.objects.all()
    serializer_class = MedicalRecordAttachmentSerializer
    parser_classes = [MultiPartParser, FormParser]
    
    def create(self, request, *args, **kwargs):
        files = request.FILES.getlist("files")  # expect "files" field
        attachments = []

        for file in files:
            serializer = self.get_serializer(data={"file": file})
            serializer.is_valid(raise_exception=True)
            attachment = serializer.save()
            attachments.append(serializer.data)

        return Response(attachments, status=status.HTTP_201_CREATED)
        
