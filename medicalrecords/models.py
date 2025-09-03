from django.db import models

from structured.fields import StructuredJSONField
from typing import List

from .schemas import ValueRate, VitalSigns, DateAndTime

class MedicalRecord(models.Model):
    patient = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='patient_records')
    hospital = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='hospital_records')
    
    chief_complaint = models.TextField()
    history = StructuredJSONField(schema=List[str])
    vital_signs = StructuredJSONField(schema=VitalSigns)
    physical_exam = StructuredJSONField(schema=List[str])
    diagnosis = StructuredJSONField(schema=List[str])
    treatment_plan = StructuredJSONField(schema=List[str])
    care_instructions = StructuredJSONField(schema=List[str])
    appointment = StructuredJSONField(schema=DateAndTime)
    
    referred_docuhealth_hosp = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='referred_medical_records')
    referred_hosp = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Medical Record for {self.patient.email} created on {self.created_at}'
    
class DrugRecord(models.Model):
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='drug_records')
    name = models.CharField(max_length=255)
    route = models.CharField(max_length=255)
    quantity = models.FloatField()
    frequency = StructuredJSONField(schema=ValueRate)
    duration = StructuredJSONField(schema=ValueRate)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    