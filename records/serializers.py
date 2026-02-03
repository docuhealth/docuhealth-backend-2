from django.db import transaction

from rest_framework import serializers

from .models import MedicalRecord, DrugRecord, MedicalRecordAttachment, VitalSigns, VitalSignsRequest, Admission, CaseNote, SoapNote, DischargeForm, SoapNoteAdditionalNotes
from .mixins import CreateSoapMultipartJsonMixin

from accounts.models import PatientProfile, SubaccountProfile, HospitalStaffProfile
from accounts.serializers import PatientFullInfoSerializer, PatientBasicInfoSerializer, HospitalStaffInfoSerilizer, HospitalStaffBasicInfoSerializer

from hospital_ops.models import Appointment
from hospital_ops.serializers import AppointmentSerializer, SoapNoteAppointmentSerializer

from organizations.serializers import HospitalBasicInfoSerializer
from organizations.models import HospitalProfile, PharmacyProfile

from facility.models import HospitalWard, WardBed
from facility.serializers import WardBedSerializer, WardNameSerializer


class ValueRateSerializer(serializers.Serializer):
    value = serializers.FloatField()
    rate = serializers.CharField()
    
class VitalSignsRequestSerializer(serializers.ModelSerializer):
    patient_hin = serializers.SlugRelatedField(slug_field="hin", source="patient", queryset=PatientProfile.objects.all(), write_only=True)
    patient = PatientFullInfoSerializer(read_only=True)
    
    staff_id = serializers.SlugRelatedField(slug_field="staff_id", source="staff", queryset=HospitalStaffProfile.objects.filter(role=HospitalStaffProfile.StaffRole.NURSE), write_only=True)
    staff = HospitalStaffInfoSerilizer(read_only=True)
    
    class Meta:
        model = VitalSignsRequest
        exclude = ['is_deleted', 'deleted_at']
        read_only_fields = ['id', 'created_at', 'processed_at', 'status', 'hospital']
        
class VitalSignsViaRequestSerializer(serializers.ModelSerializer):
    request = serializers.PrimaryKeyRelatedField(write_only=True, queryset=VitalSignsRequest.objects.all(), required=True)
    
    class Meta:
        model = VitalSigns
        exclude = ['is_deleted', 'deleted_at']
        read_only_fields = ['hospital', 'patient', 'staff', 'created_at']
        
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        
        vital_signs_request = validated_data['request']
        staff = self.context['request'].user.hospital_staff_profile
        hospital = staff.hospital
        
        if vital_signs_request.status == VitalSignsRequest.Status.PROCESSED:
            raise serializers.ValidationError({"request": f"This vital signs request has been processed already"})
        
        if vital_signs_request.staff != staff:
            raise serializers.ValidationError({"request": "This request was not assigned to this staff"})
        
        if not vital_signs_request.hospital == hospital:
            raise serializers.ValidationError({"request": "Request with provided ID not found"})
        
        return validated_data

class VitalSignsSerializer(serializers.ModelSerializer):
    patient = serializers.SlugRelatedField(slug_field="hin", queryset=PatientProfile.objects.all(), write_only=True)
    patient_info = PatientBasicInfoSerializer(read_only=True, source="patient")
    
    staff = serializers.SlugRelatedField(slug_field="staff_id", queryset=HospitalStaffProfile.objects.all(), write_only=True)
    staff_info = HospitalStaffBasicInfoSerializer(read_only=True, source="staff")
    
    last_updated = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = VitalSigns
        exclude = ['is_deleted', 'deleted_at']
        read_only_fields = ['hospital', 'created_at']
        
    def get_last_updated(self, obj):
        last_vital_signs = VitalSigns.objects.filter(patient=obj.patient, created_at__lt=obj.created_at).order_by('-created_at').first()
        return last_vital_signs.created_at if last_vital_signs else None
        
class MedRecordsVitalSignsSerializer(serializers.ModelSerializer):
    class Meta:
        model = VitalSigns
        exclude = ['is_deleted', 'deleted_at', 'staff', 'patient', 'hospital', 'created_at', 'id']
    
class DrugRecordSerializer(serializers.ModelSerializer):
    frequency = ValueRateSerializer()
    duration = ValueRateSerializer()
    allergies = serializers.ListField(child=serializers.CharField())
    
    class Meta:
        model = DrugRecord
        fields = ('name', 'route', 'quantity', 'frequency', 'duration', 'allergies')
        read_only_fields = ('id', 'created_at', 'updated_at', 'medical_record', 'status')
        
class ClientDrugRecordSerializer(serializers.ModelSerializer):
    pharm_code = serializers.SlugRelatedField(slug_field="pharm_code", queryset=PharmacyProfile.objects.all(), write_only=True, source="pharmacy", required=True)
    frequency = ValueRateSerializer()
    duration = ValueRateSerializer()
    allergies = serializers.ListField(child=serializers.CharField())
    patient = serializers.SlugRelatedField(slug_field='hin', queryset=PatientProfile.objects.all(), required=True)
    
    class Meta:
        model = DrugRecord
        fields = ('name', 'route', 'quantity', 'frequency', 'duration', 'status', 'allergies', 'patient', 'created_at', 'id', 'pharm_code')
        read_only_fields = ('id', 'created_at', 'updated_at', 'status', 'medical_record')
        
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        
        request = self.context.get('request')
        partner = request.user.pharmacy_partner  
        pharmacy = validated_data.get('pharmacy')

        if pharmacy.partner != partner:
            raise serializers.ValidationError({
                "pharm_code": "This pharmacy is not registered under your partner account."
            })
        return attrs
        
class PatientMedInfoSerializer(serializers.Serializer): 
    patient_info = PatientFullInfoSerializer()
    latest_vitals = VitalSignsSerializer(allow_null=True)
    ongoing_drugs = DrugRecordSerializer(many=True)
        
class MedicalRecordAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalRecordAttachment
        fields = "__all__"
        read_only_fields = ('id', 'updated_at', 'file_size')
        
class MedRecordAppointmentSerializer(serializers.ModelSerializer):
    staff_id = serializers.SlugRelatedField(slug_field="staff_id", queryset=HospitalStaffProfile.objects.all(), write_only=True, source="staff") 
    staff = HospitalStaffInfoSerilizer(read_only=True)
    
    class Meta:
        model = Appointment
        fields = ['staff', 'staff_id', 'scheduled_time']
        read_only_fields = ['id']

class MedicalRecordSerializer(serializers.ModelSerializer):
    patient = serializers.SlugRelatedField(slug_field="hin", queryset=PatientProfile.objects.all(), required=False, write_only=True)
    patient_info = PatientBasicInfoSerializer(read_only=True, source="patient")
    
    subaccount = serializers.SlugRelatedField(slug_field="hin", queryset=SubaccountProfile.objects.all(), required=False)
    
    doctor = serializers.SlugRelatedField(slug_field="staff_id", queryset=HospitalStaffProfile.objects.filter(role=HospitalStaffProfile.StaffRole.DOCTOR), required=False, allow_null=True, write_only=True)
    doctor_info = HospitalStaffBasicInfoSerializer(read_only=True, source="doctor")
    
    referred_docuhealth_hosp = serializers.SlugRelatedField(slug_field="hin", queryset=HospitalProfile.objects.all(), required=False, allow_null=True) 
    referred_docuhealth_hosp_info = HospitalBasicInfoSerializer(read_only=True, source="referred_docuhealth_hosp")
    
    attachments = serializers.PrimaryKeyRelatedField(many=True, queryset=MedicalRecordAttachment.objects.all(), required=False, write_only=True)
    attachments_info = MedicalRecordAttachmentSerializer(many=True, read_only=True, source="attachments")
    
    drug_records = DrugRecordSerializer(many=True, required=False, allow_null=True)
    vital_signs = MedRecordsVitalSignsSerializer(required=False, allow_null=True)
    appointment = MedRecordAppointmentSerializer(required=False, allow_null=True) 
    
    hospital_info = HospitalBasicInfoSerializer(read_only=True, source="hospital")
    
    history = serializers.ListField(child=serializers.CharField(), required=False)
    physical_exam = serializers.ListField(child=serializers.CharField(), required=False)
    diagnosis = serializers.ListField(child=serializers.CharField(), required=False)
    treatment_plan = serializers.ListField(child=serializers.CharField(), required=False)
    care_instructions = serializers.ListField(child=serializers.CharField(), required=False)
    
    class Meta:
        model = MedicalRecord
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'hospital')
        
    @transaction.atomic()
    def create(self, validated_data):
        user = self.context['request'].user
        staff = user.hospital_staff_profile
        
        drug_records_data = validated_data.pop('drug_records', [])
        attachments_data = validated_data.pop('attachments', [])
        appointment_data = validated_data.pop('appointment', None)
        vital_signs_data = validated_data.pop('vital_signs', None)
        
        hospital = validated_data.get("hospital")
        patient = validated_data.get('patient')
        
        if vital_signs_data:
            vital_signs = VitalSigns.objects.create(patient=patient, hospital=hospital, staff=staff, **vital_signs_data)
            validated_data['vital_signs'] = vital_signs
        
        medical_record = MedicalRecord.objects.create(**validated_data)
        
        for drug_data in drug_records_data:
            DrugRecord.objects.create(medical_record=medical_record, patient=patient, hospital=hospital, **drug_data)
            
        for attachment in attachments_data:
            attachment.medical_record = medical_record
            attachment.save()
            
        if appointment_data:
            Appointment.objects.create(patient=patient, medical_record=medical_record, hospital=hospital, **appointment_data) 
            
        return medical_record
    
class AdmissionSerializer(serializers.ModelSerializer):
    patient_hin = serializers.SlugRelatedField(slug_field="hin", source="patient", queryset=PatientProfile.objects.all(), write_only=True)
    patient = PatientFullInfoSerializer(read_only=True)
    
    staff_id = serializers.SlugRelatedField(slug_field="staff_id", source="staff", queryset=HospitalStaffProfile.objects.all(), write_only=True)
    staff = HospitalStaffBasicInfoSerializer(read_only=True)
    
    ward = serializers.PrimaryKeyRelatedField(queryset=HospitalWard.objects.all(), write_only=True)
    ward_info = WardNameSerializer(read_only=True, source="ward")
    
    bed = serializers.PrimaryKeyRelatedField(queryset=WardBed.objects.all(), write_only=True)
    bed_info = WardBedSerializer(read_only=True, source="bed")
    
    class Meta:
        model = Admission
        exclude = ['is_deleted', 'deleted_at', 'created_at']
        read_only_fields = ['id', 'status', 'hospital', 'admission_date', 'discharge_date']
        
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        ward = validated_data['ward']
        bed = validated_data['bed']
        
        if bed.status == WardBed.Status.REQUESTED:
            raise serializers.ValidationError({"bed": f"Admission to bed {bed.bed_number} has been requested already. Revoke the request or choose another bed"})
        
        if bed.status == WardBed.Status.OCCUPIED:
            raise serializers.ValidationError({"bed": f"Bed {bed.bed_number} is occupied"})
        
        if not bed.ward == ward:
            raise serializers.ValidationError({"ward": "Bed not available in this ward"})
        
        if not ward.hospital == self.context['request'].user.hospital_staff_profile.hospital:
            raise serializers.ValidationError({"ward": "Ward with provided ID not found"})
        
        return validated_data
    
class ConfirmAdmissionSerializer(serializers.Serializer):
    def validate(self, attrs):
        admission = self.context['admission']
        staff = self.context['request'].user.hospital_staff_profile
        hospital = staff.hospital
        
        if Admission.objects.filter(patient=admission.patient, status=Admission.Status.ACTIVE).exists():
            raise serializers.ValidationError({"detail": "Patient is already admitted"})
        
        # if admission.ward != staff.ward:
        #     raise serializers.ValidationError({"detail": "You are not assigned to this ward."})
        
        if admission.hospital != hospital:
            raise serializers.ValidationError({"detail": "Admission with the provided ID does not exist"})
        
        if admission.status != Admission.Status.PENDING:
            raise serializers.ValidationError({"detail": "This admission is either already confirmed or cancelled or the patient has been discharged"})
        
        return  super().validate(attrs)
    
class CaseNoteSerializer(serializers.ModelSerializer):
    patient = serializers.SlugRelatedField(slug_field="hin", queryset=PatientProfile.objects.all(), write_only=True)
    patient_info = PatientBasicInfoSerializer(read_only=True, source="patient")
    
    staff_info = HospitalStaffBasicInfoSerializer(read_only=True, source="staff")
    hospital_info = HospitalBasicInfoSerializer(read_only=True, source="hospital")
    
    observation = serializers.ListField(child=serializers.CharField(), required=False)
    care = serializers.ListField(child=serializers.CharField(), required=False)
    response = serializers.ListField(child=serializers.CharField(), required=False)
    abnormalities = serializers.ListField(child=serializers.CharField(), required=False)
    follow_up = serializers.ListField(child=serializers.CharField(), required=False)
    
    class Meta:
        model = CaseNote
        exclude = ['is_deleted', 'deleted_at']
        read_only_fields = ['id', 'created_at', 'hospital', 'staff']
class UpdateCaseNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseNote
        fields = ['observation', 'care', 'response', 'abnormalities', 'follow_up']
        
class SoapNoteAdditionalNotesSerializer(serializers.ModelSerializer):
    soap_note = serializers.PrimaryKeyRelatedField(queryset=SoapNote.objects.all(), write_only=True)

    class Meta:
        model = SoapNoteAdditionalNotes
        fields = ['soap_note', 'note']
        read_only_fields = ['id', 'created_at']
        

class SoapNoteSerializer(CreateSoapMultipartJsonMixin, serializers.ModelSerializer):
    patient = serializers.SlugRelatedField(slug_field="hin", queryset=PatientProfile.objects.all(), write_only=True)
    patient_info = PatientBasicInfoSerializer(read_only=True, source="patient")
    
    # staff = serializers.SlugRelatedField(slug_field="staff_id", queryset=HospitalStaffProfile.objects.all(), write_only=True)
    staff_info = HospitalStaffBasicInfoSerializer(read_only=True, source="staff")
    
    hospital_info = HospitalBasicInfoSerializer(read_only=True, source="hospital")
    
    vital_signs = serializers.PrimaryKeyRelatedField(queryset=VitalSigns.objects.all(), required=False, allow_null=True, write_only=True)
    vital_signs_info = MedRecordsVitalSignsSerializer(read_only=True, source="vital_signs")
    
    appointment = SoapNoteAppointmentSerializer(required=False, allow_null=True)
    # appointment_info = MedRecordAppointmentSerializer(read_only=True, source="appointment")
    
    drug_records = DrugRecordSerializer(many=True, required=True)
    
    drug_history_allergies = serializers.ListField(child=serializers.CharField(), required=False)
    investigations = serializers.ListField(child=serializers.CharField(), required=False)
    investigations_docs = serializers.ListField(child=serializers.DictField(), required=False)
    problems_list = serializers.ListField(child=serializers.CharField(), required=False)
    care_instructions = serializers.ListField(child=serializers.CharField(), required=True)
    general_exam = serializers.ListField(child=serializers.CharField(), required=False)
    systemic_exam = serializers.ListField(child=serializers.CharField(), required=False)
    bedside_tests = serializers.ListField(child=serializers.CharField(), required=False)
    treatment_plan = serializers.ListField(child=serializers.CharField(), required=False)
    
    referred_docuhealth_hosp = serializers.SlugRelatedField(slug_field="hin", queryset=HospitalProfile.objects.all(), required=False, allow_null=True)
    
    additional_notes = SoapNoteAdditionalNotesSerializer(many=True, required=False, read_only=True)
    
    class Meta:
        model = SoapNote
        exclude = ["is_deleted", "deleted_at"]
        read_only_fields = ['id', 'created_at', 'hospital']
        
    @transaction.atomic() 
    def create(self, validated_data):
        user = self.context['request'].user
        staff = user.hospital_staff_profile
        hospital = staff.hospital
        
        drug_records_data = validated_data.pop('drug_records', [])
        appointment_data = validated_data.pop('appointment', None)
        
        patient = validated_data.get('patient')
        
        soap_note = SoapNote.objects.create(**validated_data)
        
        for drug_data in drug_records_data:
            DrugRecord.objects.create(soap_note=soap_note, patient=patient, hospital=hospital, **drug_data, upload_source=DrugRecord.UploadSource.SOAPNOTE)
            
        if appointment_data:
            appointment = Appointment.objects.create(patient=patient, staff=staff, soap_note=soap_note, hospital=hospital, **appointment_data) 
            print(appointment)
            
        return soap_note
    
class DischargeFormSerializer(serializers.ModelSerializer):
    patient = serializers.SlugRelatedField(slug_field="hin", queryset=PatientProfile.objects.all(), write_only=True)
    patient_info = PatientBasicInfoSerializer(read_only=True, source="patient")
    
    staff = serializers.SlugRelatedField(slug_field="staff_id", queryset=HospitalStaffProfile.objects.all(), write_only=True)
    staff_info = HospitalStaffBasicInfoSerializer(read_only=True, source="staff")
    
    hospital_info = HospitalBasicInfoSerializer(read_only=True, source="hospital")
    
    condition_on_discharge = serializers.ListField(child=serializers.CharField(), required=True)
    diagnosis = serializers.ListField(child=serializers.CharField(), required=True)
    treatment_plan = serializers.ListField(child=serializers.CharField(), required=True)
    care_instructions = serializers.ListField(child=serializers.CharField(), required=True)
    
    follow_up_appointment = AppointmentSerializer(required=False, allow_null=True, write_only=True)
    follow_up_appointment_info = MedRecordAppointmentSerializer(read_only=True, source="appointment")
    
    drug_records = DrugRecordSerializer(many=True, required=True)
    
    class Meta:
        model = DischargeForm
        exclude = ['is_deleted', 'deleted_at']
        read_only_fields = ['id', 'created_at', 'hospital']
        
    @transaction.atomic() 
    def create(self, validated_data):
        user = self.context['request'].user
        staff = user.hospital_staff_profile
        
        drug_records_data = validated_data.pop('drug_records', [])
        appointment_data = validated_data.pop('follow_up_appointment', None)
        
        hospital = validated_data.get("hospital")
        patient = validated_data.get('patient')
        
        discharge_form = DischargeForm.objects.create(**validated_data)
        
        for drug_data in drug_records_data:
            DrugRecord.objects.create(discharge_form=discharge_form, patient=patient, hospital=hospital, **drug_data, upload_source=DrugRecord.UploadSource.DISCHARGEFORM)
            
        if appointment_data:
            Appointment.objects.create(patient=patient, staff=staff, discharge_form=discharge_form, hospital=hospital, **appointment_data) 
            
        return discharge_form