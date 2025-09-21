from django.db import models
from core.models import User
from cloudinary.models import CloudinaryField

from rest_framework.exceptions import ValidationError

from patients.models import PatientProfile, SubaccountProfile
from hospitals.models import HospitalProfile

class MedicalRecord(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='medical_records', null=True, blank=True)
    subaccount = models.ForeignKey(SubaccountProfile, on_delete=models.CASCADE, related_name='medical_records', null=True, blank=True)
    hospital = models.ForeignKey(HospitalProfile, on_delete=models.CASCADE, related_name='medical_records')
    
    chief_complaint = models.TextField()
    history = models.JSONField(default=list)
    vital_signs = models.JSONField(default=dict)
    physical_exam = models.JSONField(default=list)
    diagnosis = models.JSONField(default=list)
    treatment_plan = models.JSONField(default=list)
    care_instructions = models.JSONField(default=list)
    appointment = models.JSONField(default=dict, blank=True, null=True)
    
    referred_docuhealth_hosp = models.ForeignKey(HospitalProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='referred_medical_records')
    referred_hosp = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def clean(self):
        if not self.patient and not self.subaccount:
            raise ValidationError("Either patient or subaccount must be set.")
        if self.patient and self.subaccount:
            raise ValidationError("Only one of patient or subaccount can be set.")

    def __str__(self):
        return f'Medical Record for {self.patient.email} created on {self.created_at}'
    
class DrugRecord(models.Model):
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='drug_records', blank=True, null=True)
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='drug_records', blank=True, null=True)
    hospital = models.ForeignKey(HospitalProfile, on_delete=models.CASCADE, related_name='drug_records', blank=True, null=True)
    
    name = models.CharField(max_length=255)
    route = models.CharField(max_length=255)
    quantity = models.FloatField()
    
    frequency = models.JSONField(default=dict)
    duration = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
class MedicalRecordAttachment(models.Model):
    medical_record = models.ForeignKey(MedicalRecord, related_name="attachments", on_delete=models.CASCADE, null=True, blank=True)
    file = CloudinaryField("medical_records/") 
    uploaded_at = models.DateTimeField(auto_now_add=True)


    