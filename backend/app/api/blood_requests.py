import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.app.core.db import get_db
from backend.app.models.entities import BloodRequest, Hospital, Patient, Doctor
from backend.app.schemas.schemas import BloodRequestCreate, BloodRequestStatusUpdate, BloodRequestResponse
from backend.app.core.redis_client import cache_delete_pattern
from backend.app.websocket.manager import ws_manager

router = APIRouter(prefix="/api/blood-requests", tags=["Blood Requests"])

@router.get("", response_model=List[BloodRequestResponse])
async def list_blood_requests(urgency: Optional[str] = None, status_filter: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    query = select(BloodRequest).options(
        selectinload(BloodRequest.hospital),
        selectinload(BloodRequest.patient),
        selectinload(BloodRequest.doctor)
    ).order_by(BloodRequest.created_at.desc())
    
    if urgency:
        query = query.filter(BloodRequest.urgency == urgency)
    if status_filter:
        query = query.filter(BloodRequest.status == status_filter)
        
    result = await db.execute(query)
    requests = result.scalars().all()
    
    res = []
    for req in requests:
        resp = BloodRequestResponse.model_validate(req)
        resp.hospital_name = req.hospital.name if req.hospital else None
        resp.patient_name = req.patient.name if req.patient else None
        resp.doctor_name = req.doctor.name if req.doctor else None
        res.append(resp)
    return res

@router.post("", response_model=BloodRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_blood_request(req_in: BloodRequestCreate, db: AsyncSession = Depends(get_db)):
    hospital = await db.get(Hospital, req_in.hospital_id)
    if not hospital:
        raise HTTPException(status_code=400, detail="Hospital not found")
        
    patient = await db.get(Patient, req_in.patient_id)
    if not patient:
        raise HTTPException(status_code=400, detail="Patient not found")
        
    doctor_name = None
    if req_in.doctor_id:
        doctor = await db.get(Doctor, req_in.doctor_id)
        if doctor:
            doctor_name = doctor.name

    req_obj = BloodRequest(**req_in.model_dump())
    db.add(req_obj)
    await db.commit()
    await db.refresh(req_obj)
    
    await cache_delete_pattern("cache:requests:*")
    await cache_delete_pattern("cache:dashboard:*")
    
    full_group = f"{req_obj.blood_group}{req_obj.rh_factor}"
    await ws_manager.broadcast("blood_request_created", {
        "request_id": str(req_obj.id),
        "hospital_name": hospital.name,
        "patient_name": patient.name,
        "blood_group": full_group,
        "units_required": req_obj.units_required,
        "urgency": req_obj.urgency,
        "status": req_obj.status,
        "created_at": req_obj.created_at.isoformat()
    })
    
    resp = BloodRequestResponse.model_validate(req_obj)
    resp.hospital_name = hospital.name
    resp.patient_name = patient.name
    resp.doctor_name = doctor_name
    return resp

@router.get("/{request_id}", response_model=BloodRequestResponse)
async def get_blood_request(request_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(BloodRequest).options(
            selectinload(BloodRequest.hospital),
            selectinload(BloodRequest.patient),
            selectinload(BloodRequest.doctor)
        ).filter(BloodRequest.id == request_id)
    )
    req_obj = result.scalar_one_or_none()
    if not req_obj:
        raise HTTPException(status_code=404, detail="Blood request not found")
        
    resp = BloodRequestResponse.model_validate(req_obj)
    resp.hospital_name = req_obj.hospital.name if req_obj.hospital else None
    resp.patient_name = req_obj.patient.name if req_obj.patient else None
    resp.doctor_name = req_obj.doctor.name if req_obj.doctor else None
    return resp

@router.patch("/{request_id}/status", response_model=BloodRequestResponse)
async def update_blood_request_status(request_id: uuid.UUID, status_in: BloodRequestStatusUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(BloodRequest).options(
            selectinload(BloodRequest.hospital),
            selectinload(BloodRequest.patient),
            selectinload(BloodRequest.doctor)
        ).filter(BloodRequest.id == request_id)
    )
    req_obj = result.scalar_one_or_none()
    if not req_obj:
        raise HTTPException(status_code=404, detail="Blood request not found")
        
    req_obj.status = status_in.status
    await db.commit()
    await db.refresh(req_obj)
    
    await cache_delete_pattern("cache:requests:*")
    await cache_delete_pattern("cache:dashboard:*")
    
    full_group = f"{req_obj.blood_group}{req_obj.rh_factor}"
    await ws_manager.broadcast("blood_request_updated", {
        "request_id": str(req_obj.id),
        "status": req_obj.status,
        "blood_group": full_group,
        "hospital_name": req_obj.hospital.name if req_obj.hospital else ""
    })
    
    resp = BloodRequestResponse.model_validate(req_obj)
    resp.hospital_name = req_obj.hospital.name if req_obj.hospital else None
    resp.patient_name = req_obj.patient.name if req_obj.patient else None
    resp.doctor_name = req_obj.doctor.name if req_obj.doctor else None
    return resp

@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_blood_request(request_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    req_obj = await db.get(BloodRequest, request_id)
    if not req_obj:
        raise HTTPException(status_code=404, detail="Blood request not found")
        
    await db.delete(req_obj)
    await db.commit()
    
    await cache_delete_pattern("cache:requests:*")
    await cache_delete_pattern("cache:dashboard:*")
    return None
