from django.db import models

from docuhealth2.models import BaseModel

from organizations.models import HospitalProfile

class HospitalWard(BaseModel):
    name = models.CharField(max_length=100)
    hospital = models.ForeignKey(HospitalProfile, on_delete=models.CASCADE, related_name="wards")
    total_beds = models.IntegerField()
    
    def __str__(self):
        return f"Ward {self.name}"
    
    class Meta:
        db_table = 'hospitals_hospitalward'
    
    @property
    def available_beds(self):
        return self.beds.filter(status="available").count()
    
class WardBed(BaseModel):
    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        OCCUPIED = "occupied", "Occupied"
        REQUESTED = "requested", "Requested"
        
    ward = models.ForeignKey(HospitalWard, on_delete=models.CASCADE, related_name="beds")
    bed_number = models.IntegerField()  
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)
    
    class Meta:
        db_table = 'hospitals_wardbed'

    def __str__(self):
        return f"{self.ward.name} - Bed {self.bed_number}"
    
    @property
    def is_available(self):
        return self.status == self.Status.AVAILABLE