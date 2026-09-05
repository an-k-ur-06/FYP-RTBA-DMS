import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.core.db import get_db
from backend.app.models.entities import Donor
from backend.app.schemas.schemas import DonorCreate, DonorUpdate, DonorAvailabilityUpdate, DonorResponse
from backend.app.core.redis_client import cache_delete_pattern
from backend.app.websocket.manager import ws_manager

router = APIRouter(prefix="/api/donors", tags=["Donors"])

@router.get("", response_model=List[DonorResponse])
async def list_donors(blood_group: Optional[str] = None, available_only: Optional[bool] = None, db: AsyncSession = Depends(get_db)):
    query = select(Donor).order_by(Donor.name)
    if blood_group:
        query = query.filter(Donor.blood_group == blood_group.upper())
    if available_only:
        query = query.filter(Donor.is_available == True)
        
    result = await db.execute(query)
    donors = result.scalars().all()
    return donors

@router.post("", response_model=DonorResponse, status_code=status.HTTP_201_CREATED)
async def create_donor(donor_in: DonorCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Donor).filter(Donor.email == donor_in.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Donor email already registered")

    donor = Donor(**donor_in.model_dump())
    db.add(donor)
    await db.commit()
    await db.refresh(donor)
    
    await cache_delete_pattern("cache:donors:*")
    await cache_delete_pattern("cache:dashboard:*")
    
    await ws_manager.broadcast("donor_availability_updated", {
        "donor_id": str(donor.id),
        "name": donor.name,
        "is_available": donor.is_available,
        "action": "created"
    })
    
    return donor

@router.get("/{donor_id}", response_model=DonorResponse)
async def get_donor(donor_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    donor = await db.get(Donor, donor_id)
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found")
    return donor

@router.put("/{donor_id}", response_model=DonorResponse)
async def update_donor(donor_id: uuid.UUID, update_in: DonorUpdate, db: AsyncSession = Depends(get_db)):
    donor = await db.get(Donor, donor_id)
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found")
        
    for field, val in update_in.model_dump(exclude_unset=True).items():
        setattr(donor, field, val)
        
    await db.commit()
    await db.refresh(donor)
    
    await cache_delete_pattern("cache:donors:*")
    await cache_delete_pattern("cache:dashboard:*")
    
    await ws_manager.broadcast("donor_availability_updated", {
        "donor_id": str(donor.id),
        "name": donor.name,
        "is_available": donor.is_available,
        "action": "updated"
    })
    
    return donor

@router.patch("/{donor_id}/availability", response_model=DonorResponse)
async def update_donor_availability(donor_id: uuid.UUID, avail_in: DonorAvailabilityUpdate, db: AsyncSession = Depends(get_db)):
    donor = await db.get(Donor, donor_id)
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found")
        
    donor.is_available = avail_in.is_available
    await db.commit()
    await db.refresh(donor)
    
    await cache_delete_pattern("cache:donors:*")
    await cache_delete_pattern("cache:dashboard:*")
    
    await ws_manager.broadcast("donor_availability_updated", {
        "donor_id": str(donor.id),
        "name": donor.name,
        "is_available": donor.is_available,
        "action": "availability_changed"
    })
    
    return donor

@router.delete("/{donor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_donor(donor_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    donor = await db.get(Donor, donor_id)
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found")
        
    await db.delete(donor)
    await db.commit()
    
    await cache_delete_pattern("cache:donors:*")
    await cache_delete_pattern("cache:dashboard:*")
    return None
