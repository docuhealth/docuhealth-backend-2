from django.db import models

from medicalrecords.models import MedicalRecord
from hospitals.models import HospitalProfile, HospitalStaffProfile
from patients.models import PatientProfile

from docuhealth2.models import BaseModel

class Appointment(BaseModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"
        COMPLETED = "completed", "Completed"
    
    patient = models.ForeignKey(PatientProfile, related_name='appointments', on_delete=models.SET_NULL, null=True)
    medical_record = models.OneToOneField(MedicalRecord, related_name='appointment', on_delete=models.SET_NULL, null=True, blank=True)
    hospital = models.ForeignKey(HospitalProfile, related_name='appointments', on_delete=models.SET_NULL, null=True, blank=True)
    staff = models.ForeignKey(HospitalStaffProfile, related_name='appointments', on_delete=models.SET_NULL, null=True, blank=True)
    
    scheduled_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Appointment for {self.patient} with {self.staff} at {self.scheduled_time}"