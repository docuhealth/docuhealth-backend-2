from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from django.shortcuts import get_object_or_404

from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import NotFound, ValidationError

from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from docuhealth2.permissions import IsAuthenticatedHospitalAdmin, IsAuthenticatedNurse, IsAuthenticatedDoctor, IsAuthenticatedHospitalStaff, IsAuthenticatedReceptionist, IsAuthenticatedPatient
from docuhealth2.authentications import ClientHeaderAuthentication
from docuhealth2.utils.supabase import upload_files, delete_from_supabase

from .models import CaseNote, MedicalRecord, MedicalRecordAttachment, VitalSignsRequest, Admission, DrugRecord, VitalSigns, SoapNote, DischargeForm
from .serializers import CaseNoteSerializer, MedicalRecordSerializer, MedicalRecordAttachmentSerializer, VitalSignsRequestSerializer, VitalSignsViaRequestSerializer, VitalSignsSerializer, AdmissionSerializer, ConfirmAdmissionSerializer, ClientDrugRecordSerializer, DrugRecordSerializer, SoapNoteSerializer, DischargeFormSerializer, SoapNoteAdditionalNotesSerializer
from .schema import CREATE_SOAP_NOTE_SCHEMA, CREATE_DISCHARGE_FORM_SCHEMA

from facility.models import WardBed
from hospital_ops.models import HospitalPatientActivity

from accounts.models import User, HospitalStaffProfile, PatientProfile, SubaccountProfile
from accounts.serializers import PatientBasicInfoSerializer, PatientFullInfoSerializer

from organizations.models import Subscription


@extend_schema(tags=["Medical records"])  
class MedicalRecordListView(generics.ListAPIView):
    queryset = MedicalRecord.objects.all().order_by('-created_at')
    serializer_class = MedicalRecordSerializer
    permission_classes = [IsAuthenticatedHospitalStaff | IsAuthenticatedHospitalAdmin]

@extend_schema(tags=["Medical records"])  
class CreateMedicalRecordView(generics.CreateAPIView):
    queryset = MedicalRecord.objects.all()
    serializer_class = MedicalRecordSerializer
    # permission_classes = [IsAuthenticatedHospital]  
    
    def perform_create(self, serializer):
        user = self.request.user
        role = user.role
        if role == User.Role.HOSPITAL:
            serializer.save(hospital=self.request.user.hospital_profile)
            
        elif role == User.Role.HOSPITAL_STAFF:
            serializer.save(hospital=self.request.user.hospital_staff_profile.hospital)

@extend_schema(tags=["Medical records"])    
class ListUserMedicalrecordsView(generics.ListAPIView):
    serializer_class = MedicalRecordSerializer
    
    def get_queryset(self):
        user = self.request.user
        role = user.role
        
        if role == 'patient':
            return MedicalRecord.objects.filter(patient=user.patient_profile).select_related("patient", "hospital").prefetch_related("drug_records", "attachments").order_by('-created_at')
        
        if role == 'hospital':
            return MedicalRecord.objects.filter(hospital=user.hospital_profile).select_related("patient", "hospital").prefetch_related("drug_records", "attachments").order_by('-created_at')
        
        return MedicalRecord.objects.none()

@extend_schema(tags=["Medical records"])      
class UploadMedicalRecordsAttachments(generics.CreateAPIView):
    queryset = MedicalRecordAttachment.objects.all()
    serializer_class = MedicalRecordAttachmentSerializer
    parser_classes = [MultiPartParser, FormParser]
    # permission_classes = [IsAuthenticatedHospital]  
    
    def create(self, request, *args, **kwargs):
        files = request.FILES.getlist("files")  
        attachments = []

        for file in files:
            # get file size in mb and pass to the serializer
            file_size = file.size / (1024 * 1024)
            print(file_size)
            
            serializer = self.get_serializer(data={"file": file, "filename": file.name, "file_size": file_size})
            serializer.is_valid(raise_exception=True)
            attachment = serializer.save()
            attachments.append(serializer.data)
            
        attachment_ids = [attachment['id'] for attachment in attachments]
        return Response(attachment_ids, status=status.HTTP_201_CREATED)
    
@extend_schema(tags=["Doctor"], summary="Get patients medical records")
class ListPatientMedicalRecordsView(generics.ListAPIView):
    serializer_class = MedicalRecordSerializer
    permission_classes = [IsAuthenticatedDoctor]

    def get_queryset(self):
        hin = self.kwargs.get("hin")
        
        try:
            patient = PatientProfile.objects.get(hin=hin)
        except PatientProfile.DoesNotExist:
            raise NotFound({"detail": "Patient not found"})

        return MedicalRecord.objects.filter(patient=patient).order_by('-created_at')
@extend_schema(tags=["Nurse"], summary="List all vital signs request to nurse")
class ListVitalSignsRequest(generics.ListAPIView):
    serializer_class = VitalSignsRequestSerializer
    permission_classes = [IsAuthenticatedNurse]
    
    def get_queryset(self):
        staff = self.request.user.hospital_staff_profile
        return VitalSignsRequest.objects.filter(staff=staff, status=VitalSignsRequest.Status.REQUESTED).select_related("staff").order_by("-created_at")
    
@extend_schema(tags=["Nurse"], summary="Process a vital signs request")
class ProcessVitalSignsRequestView(generics.CreateAPIView):
    serializer_class = VitalSignsViaRequestSerializer
    permission_classes = [IsAuthenticatedNurse]
    
    @transaction.atomic()
    def perform_create(self, serializer):
        vital_signs_request = serializer.validated_data.pop('request')
        patient = vital_signs_request.patient
        staff = self.request.user.hospital_staff_profile
        hospital = staff.hospital
        
        serializer.save(patient=patient, staff=staff, hospital=hospital)
        
        vital_signs_request.processed_at = timezone.now()
        vital_signs_request.status = VitalSignsRequest.Status.PROCESSED
        vital_signs_request.save(update_fields=['processed_at', 'status'])
        
@extend_schema(tags=["Nurse"], summary="Update patient vital signs")
class UpdatePatientVitalSignsView(generics.CreateAPIView):
    serializer_class = VitalSignsSerializer
    permission_classes = [IsAuthenticatedNurse]
    
    @transaction.atomic()
    def perform_create(self, serializer):
        staff = self.request.user.hospital_staff_profile
        hospital = staff.hospital
        
        serializer.save(staff=staff, hospital=hospital)
        
@extend_schema(tags=["Doctor"])
class RequestVitalSignsView(generics.CreateAPIView):
    serializer_class = VitalSignsRequestSerializer
    permission_classes = [IsAuthenticatedDoctor]
    
    def perform_create(self, serializer):
        hospital = self.request.user.hospital_staff_profile.hospital
        return serializer.save(hospital=hospital)
    
@extend_schema(tags=["Hospital", "Nurse", "Doctor"], summary="List admitted patient by status")
class ListAdmittedPatientsByStatusView(generics.ListAPIView):
    serializer_class = AdmissionSerializer
    permission_classes = [IsAuthenticatedHospitalAdmin | IsAuthenticatedHospitalStaff]
    
    def get_queryset(self):
        status_param = self.kwargs.get('status')

        if status_param not in [Admission.Status.ACTIVE, Admission.Status.DISCHARGED]:
            print(Admission.Status.ACTIVE, Admission.Status.DISCHARGED, status_param)
            raise NotFound({"detail": "Invalid status parameter. Must be 'active' or 'discharged'."})

        user = self.request.user

        if hasattr(user, "hospital_profile"):
            hospital = user.hospital_profile
            return (
                Admission.objects.filter(hospital=hospital, status=status_param)
                .select_related("patient", "staff", "hospital", "ward")
                .order_by("-admission_date")
            )

        staff = user.hospital_staff_profile
        hospital = staff.hospital
        ward = getattr(staff, "ward", None)

        role = staff.role  

        base_qs = Admission.objects.filter(hospital=hospital, status=status_param).select_related("patient", "staff", "hospital", "ward")
        
        if role == HospitalStaffProfile.StaffRole.RECEPTIONIST:
            return base_qs.order_by("-admission_date")

        if role == HospitalStaffProfile.StaffRole.DOCTOR:
            return base_qs.filter(staff=staff).order_by("-admission_date")

        if role == HospitalStaffProfile.StaffRole.NURSE:
            if ward is None:
                return base_qs.filter(staff=staff).order_by("-admission_date")

            return (base_qs.filter(Q(staff=staff) | Q(ward=ward)).distinct().order_by("-admission_date"))
        
        return base_qs.filter(staff=staff).order_by("-admission_date")
    
@extend_schema(tags=['Doctor'], summary="Confirm admission of patient in a ward")
class ConfirmAdmissionView(generics.UpdateAPIView):
    serializer_class = ConfirmAdmissionSerializer
    permission_classes = [IsAuthenticatedDoctor | IsAuthenticatedReceptionist]
    lookup_url_kwarg = "admission_id"
    http_method_names = ['patch']
    
    def get_object(self):
        admission_id = self.kwargs[self.lookup_url_kwarg]
        staff = self.request.user.hospital_staff_profile

        try:
            return Admission.objects.get(id=admission_id, hospital=staff.hospital)
        
        except Admission.DoesNotExist:
            raise NotFound({"detail": "Admission not found."})
    
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        admission = self.get_object()

        serializer = self.get_serializer(data=request.data, context={"admission": admission, "request": request})
        serializer.is_valid(raise_exception=True)
        
        admission.status = Admission.Status.ACTIVE
        admission.admission_date = timezone.now()
        admission.save(update_fields=["status", "admission_date"])

        admission.bed.status = WardBed.Status.OCCUPIED
        admission.bed.save(update_fields=["status"])

        return Response({"detail": "Admission confirmed successfully."}, status=status.HTTP_200_OK)
    
@extend_schema(tags=["Nurse"], summary="Get admissions to Nurse' ward")
class ListAdmissionsView(generics.ListAPIView):
    serializer_class = AdmissionSerializer
    permission_classes = [IsAuthenticatedNurse]
    
    def get_queryset(self):
        user = self.request.user
        staff = user.hospital_staff_profile
        hospital = staff.hospital
        ward = staff.ward
        
        if not ward:
            raise ({"details": "Nurse is not assigned to any ward"})
        
        return Admission.objects.filter(hospital=hospital, ward=ward, status=Admission.Status.ACTIVE).select_related("patient", "staff", "hospital", "ward").order_by("-admission_date")
    
@extend_schema(tags=["Nurse"], summary="List all admission requests to nurses ward")
class ListAdmissionRequestsView(generics.ListAPIView):
    serializer_class = AdmissionSerializer
    permission_classes = [IsAuthenticatedNurse]
    
    def get_queryset(self):
        staff = self.request.user.hospital_staff_profile
        hospital = staff.hospital
        ward = staff.ward
        
        return Admission.objects.filter(hospital=hospital, ward=ward, status=Admission.Status.PENDING).order_by('request_date')
        
@extend_schema(tags=['Doctor', 'Receptionist'], summary="Request admission for a patient")
class RequestAdmissionView(generics.CreateAPIView):
    serializer_class = AdmissionSerializer
    permission_classes = [IsAuthenticatedDoctor | IsAuthenticatedReceptionist] 
    
    @transaction.atomic
    def perform_create(self, serializer):
        admission = serializer.save(hospital=self.request.user.hospital_staff_profile.hospital)
        
        bed = admission.bed
        bed.status = WardBed.Status.REQUESTED
        bed.save(update_fields=["status"])
        
        patient = admission.patient
        staff = self.request.user.hospital_staff_profile
        hospital = staff.hospital
        
        HospitalPatientActivity.objects.create(patient=patient, staff=staff, hospital=hospital, action="request_admission")
        
@extend_schema(tags=["Receptionist"], summary="List all admission requests that are pending")
class ListAdmissionRequestsView(generics.ListAPIView):
    serializer_class = AdmissionSerializer
    permission_classes = [IsAuthenticatedReceptionist]
    
    def get_queryset(self):
        staff = self.request.user.hospital_staff_profile
        hospital = staff.hospital
        
        return Admission.objects.filter(hospital=hospital, status=Admission.Status.PENDING).order_by('request_date')
    
@extend_schema(tags=["Doctor", "Nurse"], summary="List patients information")
class RetrievePatientInfoView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticatedDoctor | IsAuthenticatedNurse]
    serializer_class = PatientBasicInfoSerializer
    lookup_field = "hin"
    queryset = PatientProfile.objects.all()

    def retrieve(self, request, *args, **kwargs):
        patient = self.get_object()
        # patient_user = patient.user

        latest_vitals = (VitalSigns.objects.filter(patient=patient).order_by('-created_at').first())

        ongoing_drugs = DrugRecord.objects.filter(patient=patient, status=DrugRecord.Status.ONGOING) # TODO: Add status

        data = {
            "patient_info": PatientFullInfoSerializer(patient).data,
            "latest_vitals": VitalSignsSerializer(latest_vitals).data if latest_vitals else None,
            "ongoing_drugs": DrugRecordSerializer(ongoing_drugs, many=True).data,
        }

        return Response(data)

@extend_schema(tags=["Nurse"], summary="Create case notes for a patient")
class CreateCaseNotesView(generics.CreateAPIView):
    serializer_class = CaseNoteSerializer
    permission_classes = [IsAuthenticatedDoctor | IsAuthenticatedNurse]
    
    def perform_create(self, serializer):
        staff = self.request.user.hospital_staff_profile
        hospital = staff.hospital
        
        serializer.save(staff=staff, hospital=hospital)
        
@extend_schema(tags=["Nurse"], summary="List case notes for a patient")
class ListCaseNotesView(generics.ListAPIView):
    serializer_class = CaseNoteSerializer
    permission_classes = [IsAuthenticatedDoctor | IsAuthenticatedNurse]
    
    def get_queryset(self):
        hin = self.kwargs.get("hin")
        staff = self.request.user.hospital_staff_profile
        
        patient = get_object_or_404(PatientProfile, hin=hin)
        return CaseNote.objects.filter(patient=patient, hospital=staff.hospital).select_related("patient", "staff", "hospital").order_by('-created_at')
    
# @extend_schema(tags=["Nurse"], summary="Retrieve (get) a specific case note for a patient")
# class RetrieveCaseNoteView(generics.RetrieveAPIView):
#     serializer_class = UpdateCaseNoteSerializer
#     permission_classes = [IsAuthenticatedDoctor | IsAuthenticatedNurse]
    
@extend_schema(tags=["Medical records"])  
class ListSubaccountMedicalRecordsView(generics.ListAPIView):
    serializer_class = MedicalRecordSerializer
    permission_classes = [IsAuthenticatedPatient]
    
    def get_queryset(self):
        hin = self.kwargs.get("hin")
        
        if not hin:
            raise ValidationError("Subaccount hin should be provided")
        
        print(hin)
        if not SubaccountProfile.objects.filter(hin=hin).exists():
            print("Not found")
            raise NotFound("A subaccount with this HIN does not exist.")
        
        return MedicalRecord.objects.filter(subaccount__hin = hin).select_related("patient", "subaccount", "hospital").prefetch_related("drug_records", "attachments").order_by('-created_at')

@extend_schema(
    tags=["Pharmacy"],
    summary="Upload Medication Record",
    description=(
        "Submits a new drug record for a patient. Access is restricted to authorized Partners "
        "acting on behalf of a verified Pharmacy. Requires the patient's HIN (Health Identification Number) "
        "and the Pharmacy's unique PharmCode."
    ),
    parameters=[
        OpenApiParameter(
            name="X-Client-ID",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.HEADER,
            description="Your Partner Client ID",
            required=True,
        ),
        OpenApiParameter(
            name="X-Client-Secret",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.HEADER,
            description="Your Partner Secret Key",
            required=True,
        ),
    ],
    request=ClientDrugRecordSerializer,
    responses={
        201: OpenApiTypes.OBJECT,
        401: OpenApiTypes.OBJECT,
        404: OpenApiTypes.OBJECT,
    },
    examples=[
        OpenApiExample(
            'Successful Medication Upload',
            value={
                "status": "success",
                "message": "Medication record added successfully",
                "data": {
                    "record_id": 0,
                    "patient_hin": "HIN-12345678",
                    "timestamp": "2022-01-01T00:00:00.000Z"
                }
            },
            response_only=True
        )
    ]
)
class PharmacyDrugRecordUploadView(generics.CreateAPIView):
    authentication_classes = [ClientHeaderAuthentication]
    serializer_class = ClientDrugRecordSerializer
    # permission_classes = [IsAuthenticatedPharmacyClient]

    def perform_create(self, serializer):
        serializer.save(
            upload_source=DrugRecord.UploadSource.PHARMACY_API,
        )

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        
        return Response({
            "status": "success",
            "message": "Medication record added successfully",
            "data": {
                "record_id": response.data.get('id'),
                "patient_hin": request.data.get('patient'),
                "timestamp": response.data.get('created_at')
            }
        }, status=201)

class ListPatientDrugRecordsView(generics.ListAPIView):
    serializer_class = DrugRecordSerializer
    permission_classes = [IsAuthenticatedPatient]
    
    def get_queryset(self):
        patient = self.request.user.patient_profile
        return DrugRecord.objects.filter(patient=patient).order_by('-created_at')
    
@extend_schema(tags=["Medical records"], summary="Create soap note with medications and files", **CREATE_SOAP_NOTE_SCHEMA)
class CreateSoapNoteView(generics.CreateAPIView):
    serializer_class = SoapNoteSerializer
    permission_classes = [IsAuthenticatedDoctor]
    parser_classes = [MultiPartParser, FormParser]

    def create(self, request, *args, **kwargs):
        staff = self.request.user.hospital_staff_profile
        hospital = staff.hospital
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        investigation_docs = request.FILES.getlist("investigation_docs")
        uploaded_data = []
        if investigation_docs:
            uploaded_data = upload_files(investigation_docs, "soapnote_investigations")
        
        try: 
            instance = serializer.save(hospital=hospital, staff=staff, investigation_docs=uploaded_data)
            
            headers = self.get_success_headers(serializer.data)
            return Response(self.get_serializer(instance).data, status=status.HTTP_201_CREATED, headers=headers)
            
        except Exception as e:
            for doc in uploaded_data:
                delete_from_supabase(doc['path'])
            
            print(f"Soap Note Error: {str(e)}")
            raise e
        
@extend_schema(tags=["Medical records"], summary="List soap notes for a patient")
class ListPatientSoapNotesView(generics.ListAPIView):
    serializer_class = SoapNoteSerializer
    permission_classes = [IsAuthenticatedDoctor | IsAuthenticatedNurse]
    
    def get_queryset(self):
        hin = self.kwargs.get("hin")
        staff = self.request.user.hospital_staff_profile
        
        patient = get_object_or_404(PatientProfile, hin=hin)
        return SoapNote.objects.filter(patient=patient, hospital=staff.hospital).select_related("patient", "staff", "hospital").order_by('-created_at')
    
@extend_schema(tags=["Medical records"], summary="Discharge a patient", **CREATE_DISCHARGE_FORM_SCHEMA)    
class DischargePatientView(generics.CreateAPIView):
    serializer_class = DischargeFormSerializer
    permission_classes = [IsAuthenticatedDoctor | IsAuthenticatedNurse]
    parser_classes = [MultiPartParser, FormParser]
    
    def create(self, request, *args, **kwargs):
        staff = self.request.user.hospital_staff_profile
        hospital = staff.hospital
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        investigation_docs = request.FILES.getlist("investigation_docs")
        uploaded_data = []
        if investigation_docs:
            uploaded_data = upload_files(investigation_docs, "discharge_form_investigations")
        
        try:
            with transaction.atomic():
                serializer.save(hospital=hospital, staff=staff, investigation_docs=uploaded_data)
                
                admission = serializer.validated_data.get('admission')
                admission.status = Admission.Status.DISCHARGED
                admission.discharge_date = timezone.now()
                admission.save(update_fields=['status', 'discharge_date'])
                
                admission.bed.status = WardBed.Status.AVAILABLE
                admission.bed.save(update_fields=["status"])
                
                headers = self.get_success_headers(serializer.data)
                return Response({"detail": "Patient discharged successfully."}, status=status.HTTP_201_CREATED, headers=headers)
            
        except Exception as e:
            for doc in uploaded_data:
                delete_from_supabase(doc['path'])
            
            print(f"Discharge Form Error: {str(e)}")
            raise e
        
@extend_schema(tags=["Medical records"], summary="List discharge forms for a patient")
class ListPatientDischargeFormsView(generics.ListAPIView):
    serializer_class = DischargeFormSerializer
    permission_classes = [IsAuthenticatedDoctor | IsAuthenticatedNurse]
    
    def get_queryset(self):
        hin = self.kwargs.get("hin")
        staff = self.request.user.hospital_staff_profile
        
        patient = get_object_or_404(PatientProfile, hin=hin)
        return DischargeForm.objects.filter(patient=patient, hospital=staff.hospital).select_related("patient", "staff", "hospital").order_by('-created_at')
    
@extend_schema(tags=["Medical records"], summary="Create additional notes for a SOAP note")
class CreateSoapNoteAdditionalNotesView(generics.CreateAPIView):
    serializer_class = SoapNoteAdditionalNotesSerializer
    permission_classes = [IsAuthenticatedDoctor | IsAuthenticatedNurse]
    
# @extend_schema(tags=["Medical records"], summary="List additional notes for a SOAP note")
# class ListSoapNoteAdditionalNotesView(generics.ListAPIView):
#     serializer_class = SoapNoteAdditionalNotesSerializer
#     permission_classes = [IsAuthenticatedDoctor | IsAuthenticatedNurse]
    
#     def get_queryset(self):
#         soap_note_id = self.kwargs.get("soap_note_id")
#         staff = self.request.user.hospital_staff_profile
        
#         soap_note = get_object_or_404(SoapNote, id=soap_note_id, hospital=staff.hospital)
#         return SoapNoteAdditionalNotes.objects.filter(soap_note=soap_note).order_by('-created_at')