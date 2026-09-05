import uuid
from datetime import datetime, date
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Date, ForeignKey, CheckConstraint, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from backend.app.core.db import Base

class Hospital(Base):
    __tablename__ = "hospitals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)
    address = Column(String(500), nullable=False)
    city = Column(String(100), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    phone = Column(String(50), nullable=False)
    emergency_contact = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    doctors = relationship("Doctor", back_populates="hospital", cascade="all, delete-orphan")
    patients = relationship("Patient", back_populates="hospital", cascade="all, delete-orphan")
    inventory = relationship("BloodInventory", back_populates="hospital", cascade="all, delete-orphan")
    blood_requests = relationship("BloodRequest", back_populates="hospital", cascade="all, delete-orphan")
    donations = relationship("Donation", back_populates="hospital")

class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    license_number = Column(String(100), unique=True, nullable=False, index=True)
    specialization = Column(String(100), nullable=False)
    phone = Column(String(50), nullable=False)
    email = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    hospital = relationship("Hospital", back_populates="doctors")
    blood_requests = relationship("BloodRequest", back_populates="doctor")

class Patient(Base):
    __tablename__ = "patients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    medical_record_number = Column(String(100), unique=True, nullable=False, index=True)
    age = Column(Integer, nullable=False)
    gender = Column(String(20), nullable=False)
    blood_group = Column(String(10), nullable=False, index=True)
    rh_factor = Column(String(5), nullable=False)
    condition_summary = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    hospital = relationship("Hospital", back_populates="patients")
    blood_requests = relationship("BloodRequest", back_populates="patient")

class Donor(Base):
    __tablename__ = "donors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(50), nullable=False)
    blood_group = Column(String(10), nullable=False, index=True)
    rh_factor = Column(String(5), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(20), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    is_available = Column(Boolean, default=True, nullable=False, index=True)
    last_donation_date = Column(Date, nullable=True)
    total_donations = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    donations = relationship("Donation", back_populates="donor", cascade="all, delete-orphan")
    matching_results = relationship("DonorMatchingResult", back_populates="donor", cascade="all, delete-orphan")

class BloodInventory(Base):
    __tablename__ = "blood_inventory"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False, index=True)
    blood_group = Column(String(10), nullable=False, index=True)
    rh_factor = Column(String(5), nullable=False)
    available_units = Column(Integer, default=0, nullable=False)
    reserved_units = Column(Integer, default=0, nullable=False)
    minimum_threshold = Column(Integer, default=5, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("available_units >= 0", name="chk_available_units_non_negative"),
        CheckConstraint("reserved_units >= 0", name="chk_reserved_units_non_negative"),
        Index("idx_hospital_blood_group", "hospital_id", "blood_group", "rh_factor", unique=True),
    )

    # Relationships
    hospital = relationship("Hospital", back_populates="inventory")

class BloodRequest(Base):
    __tablename__ = "blood_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("doctors.id", ondelete="SET NULL"), nullable=True, index=True)
    blood_group = Column(String(10), nullable=False, index=True)
    rh_factor = Column(String(5), nullable=False)
    units_required = Column(Integer, nullable=False)
    urgency = Column(String(20), default="Medium", nullable=False, index=True) # Low, Medium, High, Critical
    status = Column(String(30), default="Pending", nullable=False, index=True) # Pending, Matching, Partially Fulfilled, Fulfilled, Cancelled
    clinical_severity = Column(Float, default=5.0, nullable=False) # Scale 1-10
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("units_required > 0", name="chk_units_required_positive"),
    )

    # Relationships
    hospital = relationship("Hospital", back_populates="blood_requests")
    patient = relationship("Patient", back_populates="blood_requests")
    doctor = relationship("Doctor", back_populates="blood_requests")
    matching_results = relationship("DonorMatchingResult", back_populates="blood_request", cascade="all, delete-orphan")

class Donation(Base):
    __tablename__ = "donations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    donor_id = Column(UUID(as_uuid=True), ForeignKey("donors.id", ondelete="CASCADE"), nullable=False, index=True)
    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False, index=True)
    blood_group = Column(String(10), nullable=False)
    rh_factor = Column(String(5), nullable=False)
    units = Column(Integer, default=1, nullable=False)
    donation_date = Column(Date, default=date.today, nullable=False)
    status = Column(String(30), default="Completed", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    donor = relationship("Donor", back_populates="donations")
    hospital = relationship("Hospital", back_populates="donations")

class DonorMatchingResult(Base):
    __tablename__ = "donor_matching_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(UUID(as_uuid=True), ForeignKey("blood_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    donor_id = Column(UUID(as_uuid=True), ForeignKey("donors.id", ondelete="CASCADE"), nullable=False, index=True)
    is_compatible = Column(Boolean, nullable=False, default=True)
    rf_suitability_score = Column(Float, nullable=False) # 0.0 to 1.0
    distance_km = Column(Float, nullable=False)
    fuzzy_priority_score = Column(Float, nullable=False) # 0 to 100
    fuzzy_priority_rank = Column(String(20), nullable=False) # Low, Medium, High, Critical
    final_rank = Column(Integer, nullable=False)
    execution_time_ms = Column(Float, default=0.0, nullable=False)
    matched_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    blood_request = relationship("BloodRequest", back_populates="matching_results")
    donor = relationship("Donor", back_populates="matching_results")
