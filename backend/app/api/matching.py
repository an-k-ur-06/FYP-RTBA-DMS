import uuid
import math
import time
from typing import List
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.app.core.db import get_db
from backend.app.models.entities import BloodRequest, Donor, Hospital, DonorMatchingResult
from backend.app.schemas.schemas import DonorMatchResponse
from backend.app.matching.compatibility import is_blood_compatible
from backend.app.ml.rf_predictor import predict_donor_suitability
from backend.app.fuzzy.priority_engine import calculate_mamdani_fuzzy_priority
from backend.app.websocket.manager import ws_manager

router = APIRouter(prefix="/api/matching", tags=["Intelligent Donor Matching"])

def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Haversine distance formula in kilometers between two GPS coordinates.
    """
    R = 6371.0 # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2.0)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 2)

@router.post("/run/{request_id}", response_model=List[DonorMatchResponse])
async def run_donor_matching(request_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    start_time = time.time()
    
    # Fetch request & hospital
    req_res = await db.execute(
        select(BloodRequest).options(selectinload(BloodRequest.hospital)).filter(BloodRequest.id == request_id)
    )
    req_obj = req_res.scalar_one_or_none()
    if not req_obj:
        raise HTTPException(status_code=404, detail="Blood request not found")
        
    hospital = req_obj.hospital
    if not hospital:
        raise HTTPException(status_code=400, detail="Request hospital reference missing")
        
    # Fetch all donors
    donor_res = await db.execute(select(Donor))
    all_donors = donor_res.scalars().all()
    
    # Delete old match results for this request if re-running
    old_matches = await db.execute(select(DonorMatchingResult).filter(DonorMatchingResult.request_id == request_id))
    for om in old_matches.scalars().all():
        await db.delete(om)
        
    match_candidates = []
    today = date.today()
    
    for donor in all_donors:
        # Step 1: Deterministic ABO & Rh compatibility check
        compatible = is_blood_compatible(donor.blood_group, donor.rh_factor, req_obj.blood_group, req_obj.rh_factor)
        if not compatible:
            continue
            
        # Step 2: Distance calculation
        dist_km = calculate_haversine_distance(donor.latitude, donor.longitude, hospital.latitude, hospital.longitude)
        
        # Step 3: Operational Eligibility Filter
        days_since_donation = (today - donor.last_donation_date).days if donor.last_donation_date else 120
        is_eligible = (18 <= donor.age <= 65) and (donor.is_available)
        
        # Step 4: Random Forest Suitability Prediction (0.0 - 1.0)
        rf_score = predict_donor_suitability(
            days_since_donation=days_since_donation,
            total_donations=donor.total_donations,
            distance_km=dist_km,
            is_available=donor.is_available
        )
        
        # Step 5: Mamdani Fuzzy Logic Prioritization (0 - 100)
        fuzzy_score, fuzzy_rank = calculate_mamdani_fuzzy_priority(
            distance_km=dist_km,
            donor_is_available=donor.is_available,
            rf_suitability_score=rf_score,
            urgency_level=req_obj.urgency
        )
        
        # Step 6: Composite Rank Score
        composite_score = 0.60 * fuzzy_score + 40.0 * rf_score
        
        match_candidates.append({
            "donor": donor,
            "compatible": compatible,
            "distance_km": dist_km,
            "rf_score": round(rf_score, 4),
            "fuzzy_score": fuzzy_score,
            "fuzzy_rank": fuzzy_rank,
            "composite_score": composite_score
        })
        
    # Sort candidates by composite score descending
    match_candidates.sort(key=lambda x: x["composite_score"], reverse=True)
    
    exec_time_ms = round((time.time() - start_time) * 1000.0, 2)
    
    response_list = []
    
    for rank, item in enumerate(match_candidates[:20], start=1):
        donor = item["donor"]
        match_id = uuid.uuid4()
        res_obj = DonorMatchingResult(
            id=match_id,
            request_id=request_id,
            donor_id=donor.id,
            is_compatible=item["compatible"],
            rf_suitability_score=item["rf_score"],
            distance_km=item["distance_km"],
            fuzzy_priority_score=item["fuzzy_score"],
            fuzzy_priority_rank=item["fuzzy_rank"],
            final_rank=rank,
            execution_time_ms=exec_time_ms
        )
        db.add(res_obj)
        
        response_list.append(DonorMatchResponse(
            id=match_id,
            request_id=request_id,
            donor_id=donor.id,
            donor_name=donor.name,
            donor_phone=donor.phone,
            donor_email=donor.email,
            blood_group=donor.blood_group,
            rh_factor=donor.rh_factor,
            is_compatible=item["compatible"],
            rf_suitability_score=item["rf_score"],
            distance_km=item["distance_km"],
            fuzzy_priority_score=item["fuzzy_score"],
            fuzzy_priority_rank=item["fuzzy_rank"],
            final_rank=rank,
            execution_time_ms=exec_time_ms,
            matched_at=datetime.utcnow()
        ))

    # Update request status to 'Matching'
    req_obj.status = "Matching"
    await db.commit()
    
    await ws_manager.broadcast("matching_completed", {
        "request_id": str(request_id),
        "total_matches": len(response_list),
        "execution_time_ms": exec_time_ms
    })
    
    return response_list

@router.get("/results/{request_id}", response_model=List[DonorMatchResponse])
async def get_matching_results(request_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DonorMatchingResult).options(
            selectinload(DonorMatchingResult.donor)
        ).filter(DonorMatchingResult.request_id == request_id).order_by(DonorMatchingResult.final_rank)
    )
    matches = result.scalars().all()
    
    res = []
    for m in matches:
        donor = m.donor
        res.append(DonorMatchResponse(
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
    return res
