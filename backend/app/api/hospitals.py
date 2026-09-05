import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.core.db import get_db
from backend.app.models.entities import Hospital
from backend.app.schemas.schemas import HospitalCreate, HospitalUpdate, HospitalResponse
from backend.app.core.redis_client import cache_delete_pattern, cache_get, cache_set
from backend.app.websocket.manager import ws_manager

router = APIRouter(prefix="/api/hospitals", tags=["Hospitals"])

@router.get("", response_model=List[HospitalResponse])
async def list_hospitals(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Hospital).order_by(Hospital.name))
    hospitals = result.scalars().all()
    return hospitals

@router.post("", response_model=HospitalResponse, status_code=status.HTTP_201_CREATED)
async def create_hospital(hospital_in: HospitalCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Hospital).filter(Hospital.code == hospital_in.code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Hospital code already exists.")
    
    hospital = Hospital(**hospital_in.model_dump())
    db.add(hospital)
    await db.commit()
    await db.refresh(hospital)

    await cache_delete_pattern("cache:dashboard:*")
    return hospital

@router.get("/{hospital_id}", response_model=HospitalResponse)
async def get_hospital(hospital_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    hospital = await db.get(Hospital, hospital_id)
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")
    return hospital

@router.put("/{hospital_id}", response_model=HospitalResponse)
async def update_hospital(hospital_id: uuid.UUID, update_in: HospitalUpdate, db: AsyncSession = Depends(get_db)):
    hospital = await db.get(Hospital, hospital_id)
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")
    
    for field, val in update_in.model_dump(exclude_unset=True).items():
        setattr(hospital, field, val)
        
    await db.commit()
    await db.refresh(hospital)
    await cache_delete_pattern("cache:dashboard:*")
    return hospital

@router.delete("/{hospital_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_hospital(hospital_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    hospital = await db.get(Hospital, hospital_id)
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")
    
    await db.delete(hospital)
    await db.commit()
    await cache_delete_pattern("cache:dashboard:*")
    return None
