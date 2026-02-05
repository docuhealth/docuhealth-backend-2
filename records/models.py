from django.db import models
from accounts.models import PatientProfile, SubaccountProfile
from cloudinary.models import CloudinaryField

from rest_framework.exceptions import ValidationError

from accounts.models import HospitalStaffProfile
from docuhealth2.models import BaseModel

from organizations.models import HospitalProfile, PharmacyProfile
from facility.models import HospitalWard, WardBed
from hospital_ops.models import Appointment

class VitalSigns(BaseModel):
    hospital = models.ForeignKey(HospitalProfile, on_delete=models.SET_NULL, related_name="vital_signs", null=True)
    patient = models.ForeignKey(PatientProfile, on_delete=models.SET_NULL, related_name="vital_signs", null=True)
    staff = models.ForeignKey(HospitalStaffProfile, on_delete=models.SET_NULL, related_name="vital_signs", null=True)
    
    blood_pressure = models.CharField(max_length=100, blank=True, null=True)
    temp = models.FloatField(max_length=100, blank=True, null=True)
    resp_rate = models.FloatField(max_length=100, blank=True, null=True)
    height = models.FloatField(max_length=100, blank=True, null=True)
    weight = models.FloatField(max_length=100, blank=True, null=True)
    heart_rate = models.FloatField(max_length=100, blank=True, null=True)
    
    class Meta:
        db_table = "hospitals_vitalsigns"
    
    def __str__(self):
        return f"Vital Signs for {self.patient.full_name} by {self.staff.full_name} ({self.staff.role})"

class MedicalRecord(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.SET_NULL, related_name='medical_records', null=True, blank=True)
    doctor = models.ForeignKey(HospitalStaffProfile, on_delete=models.SET_NULL, related_name='medical_records', null=True, blank=True)
    subaccount = models.ForeignKey(SubaccountProfile, on_delete=models.SET_NULL, related_name='medical_records', null=True, blank=True)
    hospital = models.ForeignKey(HospitalProfile, on_delete=models.SET_NULL, related_name='medical_records', null=True)
    
    chief_complaint = models.TextField()
    history = models.JSONField(default=list)
    vital_signs = models.ForeignKey(VitalSigns, on_delete=models.SET_NULL, null=True, blank=True)
    physical_exam = models.JSONField(default=list)
    diagnosis = models.JSONField(default=list)
    treatment_plan = models.JSONField(default=list)
    care_instructions = models.JSONField(default=list)
    
    referred_docuhealth_hosp = models.ForeignKey(HospitalProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='referred_medical_records')
    referred_hosp = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def clean(self):
        if not self.patient and not self.subaccount:
            raise ValidationError("Either patient or subaccount must be set.")
        if self.patient and self.subaccount:
            raise ValidationError("Only one of patient or subaccount can be set.")
        
    class Meta:
        db_table = 'medicalrecords_medicalrecord'

    def __str__(self):
        if self.patient:
            user_info = self.patient.email
        elif self.subaccount:
            user_info = f"{self.subaccount.first_name} {self.subaccount.last_name}"
        else:
            user_info = "Unknown"
        return f'Medical Record for {user_info} created on {self.created_at}'
    
class MedicalRecordAttachment(models.Model):
    medical_record = models.ForeignKey(MedicalRecord, related_name="attachments", on_delete=models.CASCADE, null=True, blank=True)
    filename = models.CharField(max_length=255, blank=True, null=True)
    file = CloudinaryField("medical_records/") 
    file_size = models.PositiveIntegerField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'medicalrecords_medicalrecordattachment'

class VitalSignsRequest(BaseModel):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        PROCESSED = "processed", "Processed"
    
    hospital = models.ForeignKey(HospitalProfile, on_delete=models.SET_NULL, related_name="vital_sign_requests", null=True)
    patient = models.ForeignKey(PatientProfile, on_delete=models.SET_NULL, related_name="vital_sign_requests", null=True)
    staff = models.ForeignKey(HospitalStaffProfile, on_delete=models.SET_NULL, related_name="vital_sign_requests", null=True)
    
    note = models.TextField(blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REQUESTED)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = "hospitals_vitalsignsrequest"
    
    def __str__(self):
        return f"Vital Signs Request for {self.patient.full_name} to {self.staff.full_name} ({self.staff.role})"
    
class Admission(BaseModel):
    class Status(models.TextChoices):
        PENDING= "pending", "Pending"
        ACTIVE = "active", "Active"
        CANCELLED = "cancelled", "Cancelled"
        DISCHARGED = "discharged", "Discharged"
    
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="admissions")
    hospital = models.ForeignKey(HospitalProfile, on_delete=models.SET_NULL, related_name="admissions", null=True)
    staff = models.ForeignKey(HospitalStaffProfile, on_delete=models.SET_NULL, related_name="admissions", null=True)
    
    ward = models.ForeignKey(HospitalWard, on_delete=models.SET_NULL, related_name="admissions", null=True)
    bed = models.ForeignKey(WardBed, on_delete=models.SET_NULL, related_name="admissions", null=True)
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    request_date = models.DateTimeField(auto_now_add=True)
    admission_date = models.DateTimeField(null=True, blank=True)
    discharge_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'hospitals_admission'
    
    def __str__(self):
        return f"Admission for {self.patient.full_name} at {self.hospital.name}"
    
class CaseNote(BaseModel):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="case_notes")
    staff = models.ForeignKey(HospitalStaffProfile, on_delete=models.SET_NULL, related_name="case_notes", null=True)
    hospital = models.ForeignKey(HospitalProfile, on_delete=models.SET_NULL, related_name="case_notes", null=True)
    
    observation = models.JSONField(default=list, blank=True, null=True)
    care = models.JSONField(default=list, blank=True, null=True)
    response = models.JSONField(default=list, blank=True, null=True)
    abnormalities = models.JSONField(default=list, blank=True, null=True)
    follow_up = models.JSONField(default=list, blank=True, null=True)
    
    def __str__(self):
        return f"Case Note for {self.patient.full_name} by {self.staff.full_name}"
    
class SoapNote(BaseModel):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="soap_notes")
    staff = models.ForeignKey(HospitalStaffProfile, on_delete=models.SET_NULL, related_name="soap_notes", null=True)
    hospital = models.ForeignKey(HospitalProfile, on_delete=models.SET_NULL, related_name="soap_notes", null=True)
    
    chief_complaint = models.TextField(blank=False, null=False)
    history_of_complain = models.TextField(blank=True, null=True)
    past_med_history = models.TextField(blank=True, null=True)
    family_history = models.TextField(blank=True, null=True)
    social_history = models.TextField(blank=True, null=True)
    other_history = models.TextField(blank=True, null=True)
    review = models.TextField(blank=True, null=True)
    
    vital_signs = models.ForeignKey(VitalSigns, on_delete=models.SET_NULL, null=True, blank=True)
    
    general_exam = models.JSONField(default=list, blank=True, null=True)
    systemic_exam = models.JSONField(default=list, blank=True, null=True)
    bedside_tests = models.JSONField(default=list, blank=True, null=True)
    investigations = models.JSONField(default=list, blank=True, null=True)
    drug_history_allergies = models.JSONField(default=list, blank=True, null=True)
    investigation_docs = models.JSONField(default=list, blank=True, null=True)
    
    primary_diagnosis = models.TextField(blank=False, null=False)
    differential_diagnosis = models.TextField(blank=True, null=True)
    problems_list = models.JSONField(default=list, blank=True, null=True)
    
    treatment_plan = models.JSONField(default=list, blank=True, null=True)
    care_instructions = models.JSONField(default=list, blank=False)
    referred_docuhealth_hosp = models.ForeignKey(HospitalProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='referred_soap_notes')
    referred_hosp = models.TextField(blank=True, null=True)
    patient_education = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"SOAP Note for {self.patient.full_name} by {self.staff.full_name}"
    
class SoapNoteAdditionalNotes(BaseModel):
    soap_note = models.ForeignKey(SoapNote, on_delete=models.CASCADE, related_name="additional_notes")
    note = models.TextField()
    
    def __str__(self):
        return f"Additional Note for SOAP Note ID {self.soap_note.id}"
    
class DischargeForm(BaseModel):
    admission = models.OneToOneField(Admission, on_delete=models.CASCADE, related_name="discharge_form")
    
    staff = models.ForeignKey(HospitalStaffProfile, on_delete=models.SET_NULL, related_name="discharge_forms", null=True)
    hospital = models.ForeignKey(HospitalProfile, on_delete=models.SET_NULL, related_name="discharge_forms", null=True)
    
    chief_complaint = models.TextField()
    condition_on_discharge = models.TextField()
    
    diagnosis = models.JSONField(default=list)
    treatment_plan = models.JSONField(default=list)
    care_instructions = models.JSONField(default=list)
    
    # drug_records
    
    investigation_docs = models.JSONField(default=list, blank=True, null=True)
    
    def __str__(self):
        return f"Discharge Form for {self.patient.full_name} by {self.staff.full_name}"
    
class DrugRecord(BaseModel):
    class Status(models.TextChoices):
        ONGOING = "ongoing", "Ongoing"
        COMPLETED = "completed", "Completed"
        STOPPED = "stopped", "Stopped"
        
    class UploadSource(models.TextChoices):
        MEDICALRECORD = "medicalrecord", "Medical Record"
        PHARMACY = "pharmacy", "Pharmacy"
        HOSPITAL = "hospital", "Hospital"
        PHARMACY_API = "pharmacy_api", "Pharmacy API"
        SOAPNOTE = "soap_note", "SOAP Note"
        DISCHARGEFORM = "discharge_form", "Discharge Form"
    
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='drug_records', blank=True, null=True)
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='drug_records', blank=True, null=True)
    hospital = models.ForeignKey(HospitalProfile, on_delete=models.CASCADE, related_name='drug_records', blank=True, null=True)
    pharmacy = models.ForeignKey(PharmacyProfile, on_delete=models.SET_NULL, related_name='drug_records', blank=True, null=True)
    soap_note = models.ForeignKey(SoapNote, on_delete=models.SET_NULL, related_name='drug_records', blank=True, null=True)
    discharge_form = models.ForeignKey(DischargeForm, on_delete=models.SET_NULL, related_name='drug_records', blank=True, null=True)

    name = models.CharField(max_length=255)
    route = models.CharField(max_length=255)
    quantity = models.FloatField()
    
    frequency = models.JSONField(default=dict)
    duration = models.JSONField(default=dict)
    allergies = models.JSONField(default=list)
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ONGOING)
    
    updated_at = models.DateTimeField(auto_now=True)
    upload_source = models.CharField(max_length=20, choices=UploadSource.choices, default=UploadSource.MEDICALRECORD)
    
    class Meta:
        db_table = 'medicalrecords_drugrecord'

    def __str__(self):
        return self.name
     