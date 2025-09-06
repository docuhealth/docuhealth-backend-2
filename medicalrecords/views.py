from rest_framework import generics

from .models import MedicalRecord
from .serializers import MedicalRecordSerializer

class MedicalRecordListView(generics.ListAPIView):
    print("MedicalRecordListCreateView initialized")
    queryset = MedicalRecord.objects.all()
    serializer_class = MedicalRecordSerializer

class MedicalRecordCreateView(generics.CreateAPIView):
    queryset = MedicalRecord.objects.all()
    serializer_class = MedicalRecordSerializer

    def perform_create(self, serializer):
        serializer.save(hospital=self.request.user)
        
        
# {
#   "patient": "4123252069857",
#   "referred_docuhealth_hosp": "4123252069857",
#   "drug_records": [
#     {
#       "frequency": {
#         "value": 0.1,
#         "rate": "string"
#       },
#       "duration": {
#         "value": 0.1,
#         "rate": "string"
#       },
#       "name": "string",
#       "route": "string",
#       "quantity": 0.1
#     }
#   ],
#   "vital_signs": {
#     "blood_pressure": "string",
#     "temp": 0.1,
#     "resp_rate": 0.1,
#     "height": 0.1,
#     "weight": 0.1,
#     "heart_rate": 0.1
#   },
#   "appointment": {
#     "date": "2019-08-24",
#     "time": "14:15:22Z"
#   },
#   "history": [
#     "string"
#   ],
#   "physical_exam": [
#     "string"
#   ],
#   "diagnosis": [
#     "string"
#   ],
#   "treatment_plan": [
#     "string"
#   ],
#   "care_instructions": [
#     "string"
#   ],
#   "chief_complaint": "string",
  
# }


