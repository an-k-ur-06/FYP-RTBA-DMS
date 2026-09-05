import uuid
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field

# --- HOSPITAL SCHEMAS ---
class HospitalBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    code: str = Field(..., min_length=2, max_length=50)
    address: str = Field(..., min_length=5, max_length=500)
    city: str = Field(..., min_length=2, max_length=100)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    phone: str = Field(..., min_length=5, max_length=50)
    emergency_contact: str = Field(..., min_length=5, max_length=50)

class HospitalCreate(HospitalBase):
    pass

class HospitalUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    address: Optional[str] = Field(None, min_length=5, max_length=500)
    city: Optional[str] = Field(None, min_length=2, max_length=100)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    phone: Optional[str] = Field(None, min_length=5, max_length=50)
    emergency_contact: Optional[str] = Field(None, min_length=5, max_length=50)

class HospitalResponse(HospitalBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- DOCTOR SCHEMAS ---
class DoctorBase(BaseModel):
    hospital_id: uuid.UUID
    name: str = Field(..., min_length=2, max_length=255)
    license_number: str = Field(..., min_length=2, max_length=100)
    specialization: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=5, max_length=50)
    email: EmailStr

class DoctorCreate(DoctorBase):
    pass

class DoctorUpdate(BaseModel):
    hospital_id: Optional[uuid.UUID] = None
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    specialization: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, min_length=5, max_length=50)
    email: Optional[EmailStr] = None

class DoctorResponse(DoctorBase):
    id: uuid.UUID
    hospital_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# --- PATIENT SCHEMAS ---
class PatientBase(BaseModel):
    hospital_id: uuid.UUID
    name: str = Field(..., min_length=2, max_length=255)
    medical_record_number: str = Field(..., min_length=2, max_length=100)
    age: int = Field(..., ge=0, le=120)
    gender: str = Field(..., min_length=1, max_length=20)
    blood_group: str = Field(..., pattern=r"^(A|B|AB|O)$")
    rh_factor: str = Field(..., pattern=r"^(\+|\-)$")
    condition_summary: Optional[str] = Field(None, max_length=500)

class PatientCreate(PatientBase):
    pass

class PatientUpdate(BaseModel):
    hospital_id: Optional[uuid.UUID] = None
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    age: Optional[int] = Field(None, ge=0, le=120)
    gender: Optional[str] = Field(None, min_length=1, max_length=20)
    blood_group: Optional[str] = Field(None, pattern=r"^(A|B|AB|O)$")
    rh_factor: Optional[str] = Field(None, pattern=r"^(\+|\-)$")
    condition_summary: Optional[str] = Field(None, max_length=500)

class PatientResponse(PatientBase):
    id: uuid.UUID
    hospital_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# --- DONOR SCHEMAS ---
class DonorBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    phone: str = Field(..., min_length=5, max_length=50)
    blood_group: str = Field(..., pattern=r"^(A|B|AB|O)$")
    rh_factor: str = Field(..., pattern=r"^(\+|\-)$")
    age: int = Field(..., ge=18, le=65)
    gender: str = Field(..., min_length=1, max_length=20)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    is_available: bool = True
    last_donation_date: Optional[date] = None

class DonorCreate(DonorBase):
    pass

class DonorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, min_length=5, max_length=50)
    blood_group: Optional[str] = Field(None, pattern=r"^(A|B|AB|O)$")
    rh_factor: Optional[str] = Field(None, pattern=r"^(\+|\-)$")
    age: Optional[int] = Field(None, ge=18, le=65)
    gender: Optional[str] = Field(None, min_length=1, max_length=20)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    is_available: Optional[bool] = None
    last_donation_date: Optional[date] = None

class DonorAvailabilityUpdate(BaseModel):
    is_available: bool

class DonorResponse(DonorBase):
    id: uuid.UUID
    total_donations: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- BLOOD INVENTORY SCHEMAS ---
class InventoryBase(BaseModel):
    hospital_id: uuid.UUID
    blood_group: str = Field(..., pattern=r"^(A|B|AB|O)$")
    rh_factor: str = Field(..., pattern=r"^(\+|\-)$")
    available_units: int = Field(..., ge=0)
    reserved_units: int = Field(0, ge=0)
    minimum_threshold: int = Field(5, ge=1)

class InventoryCreate(InventoryBase):
    pass

class InventoryUpdate(BaseModel):
    available_units: int = Field(..., ge=0)
    reserved_units: Optional[int] = Field(None, ge=0)
    minimum_threshold: Optional[int] = Field(None, ge=1)

class InventoryAllocation(BaseModel):
    hospital_id: uuid.UUID
    blood_group: str
    rh_factor: str
    units_to_allocate: int = Field(..., gt=0)

class InventoryResponse(InventoryBase):
    id: uuid.UUID
    hospital_name: Optional[str] = None
    is_low_stock: bool = False
    updated_at: datetime

    class Config:
        from_attributes = True

# --- BLOOD REQUEST SCHEMAS ---
class BloodRequestBase(BaseModel):
    hospital_id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: Optional[uuid.UUID] = None
    blood_group: str = Field(..., pattern=r"^(A|B|AB|O)$")
    rh_factor: str = Field(..., pattern=r"^(\+|\-)$")
    units_required: int = Field(..., gt=0)
    urgency: str = Field("Medium", pattern=r"^(Low|Medium|High|Critical)$")
    clinical_severity: float = Field(5.0, ge=1.0, le=10.0)

class BloodRequestCreate(BloodRequestBase):
    pass

class BloodRequestStatusUpdate(BaseModel):
    status: str = Field(..., pattern=r"^(Pending|Matching|Partially Fulfilled|Fulfilled|Cancelled)$")

class BloodRequestResponse(BloodRequestBase):
    id: uuid.UUID
    hospital_name: Optional[str] = None
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- DONATION SCHEMAS ---
class DonationCreate(BaseModel):
    donor_id: uuid.UUID
    hospital_id: uuid.UUID
    blood_group: str = Field(..., pattern=r"^(A|B|AB|O)$")
    rh_factor: str = Field(..., pattern=r"^(\+|\-)$")
    units: int = Field(1, gt=0)
    donation_date: Optional[date] = None

class DonationResponse(BaseModel):
    id: uuid.UUID
    donor_id: uuid.UUID
    donor_name: Optional[str] = None
    hospital_id: uuid.UUID
    hospital_name: Optional[str] = None
    blood_group: str
    rh_factor: str
    units: int
    donation_date: date
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- DONOR MATCHING RESULT SCHEMAS ---
class DonorMatchResponse(BaseModel):
    id: uuid.UUID
    request_id: uuid.UUID
    donor_id: uuid.UUID
    donor_name: str
    donor_phone: str
    donor_email: str
    blood_group: str
    rh_factor: str
    is_compatible: bool
    rf_suitability_score: float
    distance_km: float
    fuzzy_priority_score: float
    fuzzy_priority_rank: str
    final_rank: int
    execution_time_ms: float
    matched_at: datetime

    class Config:
        from_attributes = True

# --- DASHBOARD STATS SCHEMA ---
class DashboardStatsResponse(BaseModel):
    total_donors: int
    available_donors: int
    total_hospitals: int
    pending_requests: int
    critical_requests: int
    total_inventory_units: int
    low_inventory_count: int
    inventory_by_group: dict
    recent_requests: List[BloodRequestResponse]
    recent_matches: List[DonorMatchResponse]
