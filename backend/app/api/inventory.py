import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.app.core.db import get_db
from backend.app.models.entities import BloodInventory, Hospital
from backend.app.schemas.schemas import InventoryCreate, InventoryUpdate, InventoryAllocation, InventoryResponse
from backend.app.core.redis_client import cache_delete_pattern
from backend.app.websocket.manager import ws_manager

router = APIRouter(prefix="/api/inventory", tags=["Blood Inventory"])

@router.get("", response_model=List[InventoryResponse])
async def list_inventory(hospital_id: Optional[uuid.UUID] = None, blood_group: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    query = select(BloodInventory).options(selectinload(BloodInventory.hospital)).order_by(BloodInventory.blood_group, BloodInventory.rh_factor)
    
    if hospital_id:
        query = query.filter(BloodInventory.hospital_id == hospital_id)
    if blood_group:
        bg = blood_group.upper().replace("+", "").replace("-", "")
        rh = "+" if "+" in blood_group else ("-" if "-" in blood_group else None)
        query = query.filter(BloodInventory.blood_group == bg)
        if rh:
            query = query.filter(BloodInventory.rh_factor == rh)
            
    result = await db.execute(query)
    items = result.scalars().all()
    
    res = []
    for item in items:
        resp = InventoryResponse.model_validate(item)
        resp.hospital_name = item.hospital.name if item.hospital else None
        resp.is_low_stock = item.available_units <= item.minimum_threshold
        res.append(resp)
    return res

@router.put("/update", response_model=InventoryResponse)
async def update_inventory(inv_in: InventoryCreate, db: AsyncSession = Depends(get_db)):
    hospital = await db.get(Hospital, inv_in.hospital_id)
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")
        
    query = select(BloodInventory).filter(
        BloodInventory.hospital_id == inv_in.hospital_id,
        BloodInventory.blood_group == inv_in.blood_group,
        BloodInventory.rh_factor == inv_in.rh_factor
    )
    result = await db.execute(query)
    inv_item = result.scalar_one_or_none()
    
    if inv_item is None:
        inv_item = BloodInventory(
            hospital_id=inv_in.hospital_id,
            blood_group=inv_in.blood_group,
            rh_factor=inv_in.rh_factor,
            available_units=inv_in.available_units,
            reserved_units=inv_in.reserved_units,
            minimum_threshold=inv_in.minimum_threshold
        )
        db.add(inv_item)
    else:
        inv_item.available_units = inv_in.available_units
        inv_item.reserved_units = inv_in.reserved_units
        inv_item.minimum_threshold = inv_in.minimum_threshold
        
    await db.commit()
    await db.refresh(inv_item)
    
    await cache_delete_pattern("cache:inventory:*")
    await cache_delete_pattern("cache:dashboard:*")
    
    full_group = f"{inv_item.blood_group}{inv_item.rh_factor}"
    await ws_manager.broadcast("inventory_updated", {
        "hospital_id": str(hospital.id),
        "hospital_name": hospital.name,
        "blood_group": full_group,
        "available_units": inv_item.available_units,
        "reserved_units": inv_item.reserved_units,
        "is_low_stock": inv_item.available_units <= inv_item.minimum_threshold
    })
    
    resp = InventoryResponse.model_validate(inv_item)
    resp.hospital_name = hospital.name
    resp.is_low_stock = inv_item.available_units <= inv_item.minimum_threshold
    return resp

@router.post("/allocate", response_model=InventoryResponse)
async def allocate_inventory(alloc_in: InventoryAllocation, db: AsyncSession = Depends(get_db)):
    query = select(BloodInventory).filter(
        BloodInventory.hospital_id == alloc_in.hospital_id,
        BloodInventory.blood_group == alloc_in.blood_group,
        BloodInventory.rh_factor == alloc_in.rh_factor
    )
    result = await db.execute(query)
    inv_item = result.scalar_one_or_none()
    
    if not inv_item:
        raise HTTPException(status_code=404, detail="No inventory record found for specified blood group")
        
    if inv_item.available_units < alloc_in.units_to_allocate:
        raise HTTPException(status_code=400, detail=f"Insufficient available units. Current: {inv_item.available_units}, Requested: {alloc_in.units_to_allocate}")
        
    inv_item.available_units -= alloc_in.units_to_allocate
    inv_item.reserved_units += alloc_in.units_to_allocate
    
    await db.commit()
    await db.refresh(inv_item)
    
    hospital = await db.get(Hospital, inv_item.hospital_id)
    
    await cache_delete_pattern("cache:inventory:*")
    await cache_delete_pattern("cache:dashboard:*")
    
    full_group = f"{inv_item.blood_group}{inv_item.rh_factor}"
    await ws_manager.broadcast("inventory_updated", {
        "hospital_id": str(inv_item.hospital_id),
        "hospital_name": hospital.name if hospital else "",
        "blood_group": full_group,
        "available_units": inv_item.available_units,
        "reserved_units": inv_item.reserved_units,
        "action": "allocation"
    })
    
    resp = InventoryResponse.model_validate(inv_item)
    resp.hospital_name = hospital.name if hospital else None
    resp.is_low_stock = inv_item.available_units <= inv_item.minimum_threshold
    return resp
