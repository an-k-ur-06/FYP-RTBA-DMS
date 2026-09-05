import json
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.orm import selectinload

from backend.app.core.db import get_db
from backend.app.models.entities import Donor, Hospital, BloodRequest, BloodInventory, DonorMatchingResult
from backend.app.schemas.schemas import DashboardStatsResponse, BloodRequestResponse, DonorMatchResponse
from backend.app.core.redis_client import cache_get, cache_set

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    # Try Redis cache first
    cached = await cache_get("cache:dashboard:stats")
    if cached:
        try:
            return json.loads(cached)
        except Exception:
            pass

    # Total Donors
    t_donors = await db.scalar(select(func.count(Donor.id)))
    # Available Donors
    a_donors = await db.scalar(select(func.count(Donor.id)).filter(Donor.is_available == True))
    # Total Hospitals
    t_hospitals = await db.scalar(select(func.count(Hospital.id)))
    # Pending Requests
    p_requests = await db.scalar(select(func.count(BloodRequest.id)).filter(BloodRequest.status == "Pending"))
    # Critical Requests
    c_requests = await db.scalar(select(func.count(BloodRequest.id)).filter(BloodRequest.urgency == "Critical", BloodRequest.status != "Fulfilled"))
    
    # Inventory metrics
    inv_res = await db.execute(select(BloodInventory))
    inventories = inv_res.scalars().all()
    
    t_units = sum(inv.available_units for inv in inventories)
    low_count = sum(1 for inv in inventories if inv.available_units <= inv.minimum_threshold)
    
    group_map = {}
    for inv in inventories:
        group_key = f"{inv.blood_group}{inv.rh_factor}"
        group_map[group_key] = group_map.get(group_key, 0) + inv.available_units
        
    # Recent requests
    req_query = await db.execute(
        select(BloodRequest).options(
            selectinload(BloodRequest.hospital),
            selectinload(BloodRequest.patient),
            selectinload(BloodRequest.doctor)
        ).order_by(BloodRequest.created_at.desc()).limit(5)
    )
    recent_reqs_obj = req_query.scalars().all()
    recent_requests = []
    for req in recent_reqs_obj:
        resp = BloodRequestResponse.model_validate(req)
        resp.hospital_name = req.hospital.name if req.hospital else None
        resp.patient_name = req.patient.name if req.patient else None
        resp.doctor_name = req.doctor.name if req.doctor else None
        recent_requests.append(resp)
        
    # Recent match results
    match_query = await db.execute(
        select(DonorMatchingResult).options(
            selectinload(DonorMatchingResult.donor)
        ).order_by(DonorMatchingResult.matched_at.desc()).limit(5)
    )
    recent_matches_obj = match_query.scalars().all()
    recent_matches = []
    for m in recent_matches_obj:
        donor = m.donor
        recent_matches.append(DonorMatchResponse(
            id=m.id,
            request_id=m.request_id,
            donor_id=m.donor_id,
            donor_name=donor.name if donor else "Unknown",
            donor_phone=donor.phone if donor else "",
            donor_email=donor.email if donor else "",
            blood_group=donor.blood_group if donor else "",
            rh_factor=donor.rh_factor if donor else "",
            is_compatible=m.is_compatible,
            rf_suitability_score=m.rf_suitability_score,
            distance_km=m.distance_km,
            fuzzy_priority_score=m.fuzzy_priority_score,
            fuzzy_priority_rank=m.fuzzy_priority_rank,
            final_rank=m.final_rank,
            execution_time_ms=m.execution_time_ms,
            matched_at=m.matched_at
        ))
        
    payload = {
        "total_donors": t_donors or 0,
        "available_donors": a_donors or 0,
        "total_hospitals": t_hospitals or 0,
        "pending_requests": p_requests or 0,
        "critical_requests": c_requests or 0,
        "total_inventory_units": t_units,
        "low_inventory_count": low_count,
        "inventory_by_group": group_map,
        "recent_requests": [r.model_dump(mode="json") for r in recent_requests],
        "recent_matches": [m.model_dump(mode="json") for m in recent_matches]
    }
    
    await cache_set("cache:dashboard:stats", payload, ttl_seconds=60)
    return payload
