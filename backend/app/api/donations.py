import uuid
from typing import List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.app.core.db import get_db
from backend.app.models.entities import Donation, Donor, Hospital, BloodInventory
from backend.app.schemas.schemas import DonationCreate, DonationResponse
from backend.app.core.redis_client import cache_delete_pattern
from backend.app.websocket.manager import ws_manager

router = APIRouter(prefix="/api/donations", tags=["Donations"])

@router.get("", response_model=List[DonationResponse])
async def list_donations(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Donation).options(
            selectinload(Donation.donor),
            selectinload(Donation.hospital)
        ).order_by(Donation.donation_date.desc())
    )
    donations = result.scalars().all()
    
    res = []
    for d in donations:
        resp = DonationResponse.model_validate(d)
        resp.donor_name = d.donor.name if d.donor else None
        resp.hospital_name = d.hospital.name if d.hospital else None
        res.append(resp)
    return res

@router.post("", response_model=DonationResponse, status_code=status.HTTP_201_CREATED)
async def create_donation(donation_in: DonationCreate, db: AsyncSession = Depends(get_db)):
    donor = await db.get(Donor, donation_in.donor_id)
    if not donor:
        raise HTTPException(status_code=400, detail="Donor not found")
        
    hospital = await db.get(Hospital, donation_in.hospital_id)
    if not hospital:
        raise HTTPException(status_code=400, detail="Hospital not found")

    donation = Donation(
        donor_id=donation_in.donor_id,
        hospital_id=donation_in.hospital_id,
        blood_group=donation_in.blood_group,
        rh_factor=donation_in.rh_factor,
        units=donation_in.units,
        donation_date=donation_in.donation_date or date.today(),
        status="Completed"
    )
    db.add(donation)

    # Update Donor recency & total donation count
    donor.total_donations += donation_in.units
    donor.last_donation_date = donation.donation_date
    
    # Automatically increase Hospital Blood Inventory
    query_inv = select(BloodInventory).filter(
        BloodInventory.hospital_id == donation_in.hospital_id,
        BloodInventory.blood_group == donation_in.blood_group,
        BloodInventory.rh_factor == donation_in.rh_factor
    )
    res_inv = await db.execute(query_inv)
    inv_item = res_inv.scalar_one_or_none()
    
    if inv_item:
        inv_item.available_units += donation_in.units
    else:
        inv_item = BloodInventory(
            hospital_id=donation_in.hospital_id,
            blood_group=donation_in.blood_group,
            rh_factor=donation_in.rh_factor,
            available_units=donation_in.units,
            minimum_threshold=5
        )
        db.add(inv_item)

    await db.commit()
    await db.refresh(donation)
    
    await cache_delete_pattern("cache:inventory:*")
    await cache_delete_pattern("cache:donors:*")
    await cache_delete_pattern("cache:dashboard:*")
    
    full_group = f"{donation_in.blood_group}{donation_in.rh_factor}"
    await ws_manager.broadcast("inventory_updated", {
        "hospital_id": str(hospital.id),
        "hospital_name": hospital.name,
        "blood_group": full_group,
        "available_units": inv_item.available_units,
        "action": "donation_received"
    })
    
    resp = DonationResponse.model_validate(donation)
    resp.donor_name = donor.name
    resp.hospital_name = hospital.name
    return resp
