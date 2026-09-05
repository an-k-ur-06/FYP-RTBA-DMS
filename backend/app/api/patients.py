import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.app.core.db import get_db
from backend.app.models.entities import Patient, Hospital
from backend.app.schemas.schemas import PatientCreate, PatientUpdate, PatientResponse

router = APIRouter(prefix="/api/patients", tags=["Patients"])

@router.get("", response_model=List[PatientResponse])
async def list_patients(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Patient).options(selectinload(Patient.hospital)).order_by(Patient.name))
    patients = result.scalars().all()
    res = []
    for p in patients:
        p_dict = PatientResponse.model_validate(p)
        p_dict.hospital_name = p.hospital.name if p.hospital else None
        res.append(p_dict)
    return res

@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(patient_in: PatientCreate, db: AsyncSession = Depends(get_db)):
    hospital = await db.get(Hospital, patient_in.hospital_id)
    if not hospital:
        raise HTTPException(status_code=400, detail="Hospital not found")
        
    existing = await db.execute(select(Patient).filter(Patient.medical_record_number == patient_in.medical_record_number))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Medical Record Number already exists")

    patient = Patient(**patient_in.model_dump())
    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    
    resp = PatientResponse.model_validate(patient)
    resp.hospital_name = hospital.name
    return resp

@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(patient_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Patient).options(selectinload(Patient.hospital)).filter(Patient.id == patient_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")
    resp = PatientResponse.model_validate(p)
    resp.hospital_name = p.hospital.name if p.hospital else None
    return resp

@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(patient_id: uuid.UUID, update_in: PatientUpdate, db: AsyncSession = Depends(get_db)):
    p = await db.get(Patient, patient_id)
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")
        
    for field, val in update_in.model_dump(exclude_unset=True).items():
        setattr(p, field, val)
        
    await db.commit()
    await db.refresh(p)
    
    hospital = await db.get(Hospital, p.hospital_id)
    resp = PatientResponse.model_validate(p)
    resp.hospital_name = hospital.name if hospital else None
    return resp

@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(patient_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    p = await db.get(Patient, patient_id)
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")
    await db.delete(p)
    await db.commit()
    return None
