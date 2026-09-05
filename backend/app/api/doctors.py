import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.app.core.db import get_db
from backend.app.models.entities import Doctor, Hospital
from backend.app.schemas.schemas import DoctorCreate, DoctorUpdate, DoctorResponse

router = APIRouter(prefix="/api/doctors", tags=["Doctors"])

@router.get("", response_model=List[DoctorResponse])
async def list_doctors(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Doctor).options(selectinload(Doctor.hospital)).order_by(Doctor.name))
    doctors = result.scalars().all()
    res = []
    for d in doctors:
        d_dict = DoctorResponse.model_validate(d)
        d_dict.hospital_name = d.hospital.name if d.hospital else None
        res.append(d_dict)
    return res

@router.post("", response_model=DoctorResponse, status_code=status.HTTP_201_CREATED)
async def create_doctor(doc_in: DoctorCreate, db: AsyncSession = Depends(get_db)):
    hospital = await db.get(Hospital, doc_in.hospital_id)
    if not hospital:
        raise HTTPException(status_code=400, detail="Associated hospital not found")
        
    existing = await db.execute(select(Doctor).filter(Doctor.license_number == doc_in.license_number))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Doctor license number already exists")

    doc = Doctor(**doc_in.model_dump())
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    
    resp = DoctorResponse.model_validate(doc)
    resp.hospital_name = hospital.name
    return resp

@router.get("/{doctor_id}", response_model=DoctorResponse)
async def get_doctor(doctor_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Doctor).options(selectinload(Doctor.hospital)).filter(Doctor.id == doctor_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Doctor not found")
    resp = DoctorResponse.model_validate(doc)
    resp.hospital_name = doc.hospital.name if doc.hospital else None
    return resp

@router.put("/{doctor_id}", response_model=DoctorResponse)
async def update_doctor(doctor_id: uuid.UUID, update_in: DoctorUpdate, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Doctor, doctor_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Doctor not found")
        
    for field, val in update_in.model_dump(exclude_unset=True).items():
        setattr(doc, field, val)
        
    await db.commit()
    await db.refresh(doc)
    
    hospital = await db.get(Hospital, doc.hospital_id)
    resp = DoctorResponse.model_validate(doc)
    resp.hospital_name = hospital.name if hospital else None
    return resp

@router.delete("/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_doctor(doctor_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Doctor, doctor_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Doctor not found")
    await db.delete(doc)
    await db.commit()
    return None
