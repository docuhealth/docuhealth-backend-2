from django.db import models

from docuhealth2.models import BaseModel

from accounts.models import HospitalStaffProfile, PatientProfile
from organizations.models import HospitalProfile
from docuhealth2.models import BaseModel

class HospitalPatientActivity(BaseModel):
    hospital = models.ForeignKey("organizations.HospitalProfile", on_delete=models.CASCADE)
    staff = models.ForeignKey(HospitalStaffProfile, on_delete=models.SET_NULL, null=True)
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE)

    action = models.CharField(max_length=100)  

    class Meta:
        db_table = 'hospitals_hospitalpatientactivity'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['hospital', 'staff', 'created_at']),
        ]
        
class Appointment(BaseModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"
        COMPLETED = "completed", "Completed"
    
    patient = models.ForeignKey(PatientProfile, related_name='appointments', on_delete=models.SET_NULL, null=True)
    medical_record = models.OneToOneField("records.MedicalRecord", related_name='appointment', on_delete=models.SET_NULL, null=True, blank=True)
    hospital = models.ForeignKey(HospitalProfile, related_name='appointments', on_delete=models.SET_NULL, null=True, blank=True)
    staff = models.ForeignKey(HospitalStaffProfile, related_name='appointments', on_delete=models.SET_NULL, null=True, blank=True)
    soap_note = models.ForeignKey("records.SoapNote", related_name='appointments', on_delete=models.SET_NULL, null=True, blank=True)
    discharge_form = models.ForeignKey("records.DischargeForm", related_name='appointments', on_delete=models.SET_NULL, null=True, blank=True)
    
    type = models.CharField(max_length=20, blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    
    scheduled_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'appointments_appointment'
        
    def __str__(self):
        return f"Appointment for {self.patient} with {self.staff} at {self.scheduled_time}"
    
class HandOverLog(BaseModel):
    from_nurse = models.ForeignKey(HospitalStaffProfile, related_name='handovers_given', on_delete=models.CASCADE)
    to_nurse = models.ForeignKey(HospitalStaffProfile, related_name='handovers_received', on_delete=models.CASCADE)
    
    handover_appointments = models.BooleanField(default=False)
    handover_patients = models.BooleanField(default=False)
    
    items_transferred = models.JSONField()
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"HandOver from {self.from_nurse} to {self.to_nurse} at {self.created_at}"