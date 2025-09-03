from rest_framework import generics

from .models import MedicalRecord
from .serializers import MedicalRecordSerializer

class MedicalRecordListView(generics.ListAPIView):
    print("MedicalRecordListCreateView initialized")
    queryset = MedicalRecord.objects.all()
    serializer_class = MedicalRecordSerializer

class MedicalRecordCreateView(generics.CreateAPIView):
    print("MedicalRecordListCreateView initialized")
    queryset = MedicalRecord.objects.all()
    serializer_class = MedicalRecordSerializer

    def perform_create(self, serializer):
        serializer.save(hospital=self.request.user)
        

