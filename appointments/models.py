from django.db import models

from medicalrecords.models import MedicalRecord
from hospitals.models import DoctorProfile, HospitalProfile
from patients.models import PatientProfile

class Appointment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"
        COMPLETED = "completed", "Completed"
    
    patient = models.ForeignKey(PatientProfile, related_name='appointments', on_delete=models.SET_NULL, null=True)
    medical_record = models.ForeignKey(MedicalRecord, related_name='appointments', on_delete=models.SET_NULL, null=True, blank=True)
    hospital = models.ForeignKey(HospitalProfile, related_name='appointments', on_delete=models.SET_NULL, null=True, blank=True)
    doctor = models.ForeignKey(DoctorProfile, related_name='appointments', on_delete=models.SET_NULL, null=True, blank=True)
    
    scheduled_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Appointment for {self.patient} with {self.doctor} at {self.scheduled_time}"