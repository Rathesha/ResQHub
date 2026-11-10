import os
import datetime
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# ----------------- Database Setup -----------------
DATABASE_URL = "sqlite:///./emergency.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    location = Column(String(255), nullable=False)
    people_affected = Column(Integer, default=0, nullable=False)
    contact_info = Column(String(255), nullable=True)
    severity = Column(String(50), nullable=False)
    status = Column(String(50), default="Reported", nullable=False) # Reported, Pending, In Progress, Resolved
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----------------- Automated Severity Classification Engine -----------------
def classify_severity(category: str, people_affected: int) -> str:
    """
    Automated Severity Classification Engine:
    Assigns Low, Medium, High, or Critical based on category risk matrix
    and the number of people affected.
    """
    cat = (category or "").strip().lower()
    count = max(0, people_affected or 0)

    # Categories with inherently life-threatening acute risk
    critical_categories = ["building collapse", "fire emergency", "flood"]
    urgent_categories = ["road accident", "medical emergency"]

    # Rule 1: Mass casualty / high-impact threshold
    if count >= 10:
        return "Critical"

    # Rule 2: Severe threats with multiple persons or critical categories
    if cat in critical_categories:
        if count >= 3:
            return "Critical"
        elif count >= 1:
            return "High"
        else:
            return "Medium"

    # Rule 3: Medical / Road Accident thresholds
    if cat in urgent_categories:
        if count >= 5:
            return "Critical"
        elif count >= 2:
            return "High"
        elif count == 1:
            return "Medium"
        else:
            return "Low"

    # Rule 4: Other / General hazards
    if count >= 5:
        return "High"
    elif count >= 2:
        return "Medium"
    else:
        return "Low"

# ----------------- Pydantic Schemas -----------------
class IncidentCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=5)
    category: str
    location: str = Field(..., min_length=2, max_length=255)
    people_affected: int = Field(default=0, ge=0)
    contact_info: Optional[str] = None

class IncidentStatusUpdate(BaseModel):
    status: str

class IncidentResponse(BaseModel):
    id: int
    title: str
    description: str
    category: str
    location: str
    people_affected: int
    contact_info: Optional[str]
    severity: str
    status: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True

class StatsResponse(BaseModel):
    total_incidents: int
    critical_incidents: int
    pending_incidents: int
    resolved_incidents: int
    in_progress_incidents: int
    reported_incidents: int
    category_breakdown: dict[str, int]
    severity_breakdown: dict[str, int]

# ----------------- FastAPI App -----------------
app = FastAPI(
    title="Emergency Response & Disaster Management Platform",
    description="Backend API with Automated Severity Classification and Incident Management",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.datetime.utcnow().isoformat()}

@app.post("/api/incidents", response_model=IncidentResponse, status_code=201)
def report_incident(payload: IncidentCreate, db: Session = Depends(get_db)):
    """Module 1 & 2: Public reporting with automatic severity classification"""
    calculated_severity = classify_severity(payload.category, payload.people_affected)
    
    incident = Incident(
        title=payload.title,
        description=payload.description,
        category=payload.category,
        location=payload.location,
        people_affected=payload.people_affected,
        contact_info=payload.contact_info,
        severity=calculated_severity,
        status="Reported"
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident

@app.get("/api/incidents", response_model=List[IncidentResponse])
def get_incidents(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Module 3: Retrieve incidents with optional filtering"""
    query = db.query(Incident)
    if status and status != "All":
        query = query.filter(Incident.status == status)
    if severity and severity != "All":
        query = query.filter(Incident.severity == severity)
    if category and category != "All":
        query = query.filter(Incident.category == category)
    if search:
        search_fmt = f"%{search}%"
        query = query.filter(
            (Incident.title.ilike(search_fmt)) |
            (Incident.location.ilike(search_fmt)) |
            (Incident.description.ilike(search_fmt))
        )
    
    # Sort order: Critical first, then by recency
    # We can fetch and order by id desc
    return query.order_by(Incident.id.desc()).all()

@app.get("/api/incidents/{incident_id}", response_model=IncidentResponse)
def get_incident_by_id(incident_id: int, db: Session = Depends(get_db)):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident

@app.patch("/api/incidents/{incident_id}/status", response_model=IncidentResponse)
def update_incident_status(incident_id: int, payload: IncidentStatusUpdate, db: Session = Depends(get_db)):
    """Module 3: Update incident status (Reported, Pending, In Progress, Resolved)"""
    allowed_statuses = ["Reported", "Pending", "In Progress", "Resolved"]
    if payload.status not in allowed_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {allowed_statuses}")
    
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    incident.status = payload.status
    incident.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(incident)
    return incident

@app.delete("/api/incidents/{incident_id}", status_code=200)
def delete_incident(incident_id: int, db: Session = Depends(get_db)):
    """Module 3: Delete incident or test records"""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    db.delete(incident)
    db.commit()
    return {"message": f"Incident #{incident_id} successfully deleted", "id": incident_id}

@app.get("/api/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    """Module 3: Summary analytics for admin dashboard cards and category breakdown"""
    incidents = db.query(Incident).all()
    
    total = len(incidents)
    critical = sum(1 for i in incidents if i.severity == "Critical")
    pending = sum(1 for i in incidents if i.status == "Pending")
    resolved = sum(1 for i in incidents if i.status == "Resolved")
    in_progress = sum(1 for i in incidents if i.status == "In Progress")
    reported = sum(1 for i in incidents if i.status == "Reported")

    categories = ["Fire Emergency", "Road Accident", "Medical Emergency", "Flood", "Building Collapse", "Other"]
    cat_counts = {cat: 0 for cat in categories}
    for inc in incidents:
        c = inc.category if inc.category in cat_counts else "Other"
        cat_counts[c] = cat_counts.get(c, 0) + 1

    severities = ["Critical", "High", "Medium", "Low"]
    sev_counts = {sev: 0 for sev in severities}
    for inc in incidents:
        s = inc.severity if inc.severity in sev_counts else "Low"
        sev_counts[s] = sev_counts.get(s, 0) + 1

    return {
        "total_incidents": total,
        "critical_incidents": critical,
        "pending_incidents": pending,
        "resolved_incidents": resolved,
        "in_progress_incidents": in_progress,
        "reported_incidents": reported,
        "category_breakdown": cat_counts,
        "severity_breakdown": sev_counts
    }

# ----------------- Seed Mock Data if empty -----------------
@app.on_event("startup")
def seed_data_if_empty():
    db = SessionLocal()
    try:
        count = db.query(Incident).count()
        if count == 0:
            mock_incidents = [
                {
                    "title": "Industrial Warehouse Chemical Fire",
                    "description": "Dense smoke and rapidly spreading flames reported in Sector 4 industrial area. Toxic fumes observed.",
                    "category": "Fire Emergency",
                    "location": "Sector 4 Industrial Park, Warehouse B2",
                    "people_affected": 14,
                    "contact_info": "+1-555-0192 (Plant Safety Officer)",
                    "status": "In Progress"
                },
                {
                    "title": "Multi-Vehicle Collision on Interstate Highway",
                    "description": "5 cars and 1 freight truck pile-up amid heavy fog. Traffic completely halted, medical triage required.",
                    "category": "Road Accident",
                    "location": "Interstate 95, Mile Marker 42 Northbound",
                    "people_affected": 8,
                    "contact_info": "+1-555-0381 (Highway Patrol Dispatch)",
                    "status": "Pending"
                },
                {
                    "title": "Old Residential Complex Balcony & Wall Collapse",
                    "description": "Portion of 3rd floor balcony and outer support beam collapsed onto ground alleyway. Structural integrity compromised.",
                    "category": "Building Collapse",
                    "location": "88 Elm Street, Downtown District",
                    "people_affected": 4,
                    "contact_info": "+1-555-0472 (Resident Council)",
                    "status": "Reported"
                },
                {
                    "title": "Severe Flash Flooding Submerging Residential Avenue",
                    "description": "Heavy rainfall breached local stormwater canal, 3 feet of water entered basement levels and ground floors.",
                    "category": "Flood",
                    "location": "Riverside Boulevard, Blocks 12-15",
                    "people_affected": 25,
                    "contact_info": "+1-555-0619 (Community Leader)",
                    "status": "In Progress"
                },
                {
                    "title": "Cardiac Arrest at Central Metro Station",
                    "description": "Commuter collapsed near escalator on Platform 2. First aid CPR currently being administered by station staff.",
                    "category": "Medical Emergency",
                    "location": "Central Metro Station, Platform 2",
                    "people_affected": 1,
                    "contact_info": "+1-555-0724 (Metro Security Office)",
                    "status": "Resolved"
                },
                {
                    "title": "Gas Leak Smell Near Elementary School",
                    "description": "Strong odor of natural gas detected along perimeter fence of Maple Grove Elementary. Precautionary evaluation underway.",
                    "category": "Other",
                    "location": "Maple Grove Elementary School, North Gate",
                    "people_affected": 2,
                    "contact_info": "+1-555-0883 (School Administration)",
                    "status": "Reported"
                }
            ]
            for item in mock_incidents:
                sev = classify_severity(item["category"], item["people_affected"])
                inc = Incident(
                    title=item["title"],
                    description=item["description"],
                    category=item["category"],
                    location=item["location"],
                    people_affected=item["people_affected"],
                    contact_info=item["contact_info"],
                    severity=sev,
                    status=item["status"]
                )
                db.add(inc)
            db.commit()
            print("Successfully seeded initial disaster management mock records.")
    finally:
        db.close()
