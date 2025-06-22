from fastapi import FastAPI, HTTPException, Depends, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta
import os
import random
from typing import List, Optional
import json
from dotenv import load_dotenv
load_dotenv()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/standup_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Models
class TeamMember(Base):
    __tablename__ = "team_members"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    emoji = Column(String, default="👤")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class SpinOrder(Base):
    __tablename__ = "spin_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    member_id = Column(Integer, index=True)
    position = Column(Integer)
    twist_type = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class StandupSession(Base):
    __tablename__ = "standup_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.utcnow)
    members_present = Column(String)  # JSON string of member IDs
    twist_type = Column(String, default="random")  # random, reverse, skip_one, etc.

class StandupOrder(Base):
    __tablename__ = "standup_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, index=True)
    member_id = Column(Integer, index=True)
    member_name = Column(String)
    order_position = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic models
class MemberCreate(BaseModel):
    name: str
    emoji: str = "👤"

class MemberResponse(BaseModel):
    id: int
    name: str
    emoji: str
    is_active: bool

class SpinRequest(BaseModel):
    present_members: List[int]
    twist_type: str = "random"

class StatsResponse(BaseModel):
    member_name: str
    emoji: str
    first_count: int
    last_count: int
    total_standups: int
    avg_position: float

# FastAPI app
app = FastAPI(title="Standup Spinner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080", "*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Twist functions
def apply_twist(members: List[dict], twist_type: str) -> tuple:
    """Apply different twists to the member order"""
    original_order = members.copy()
    
    if twist_type == "reverse":
        # Reverse alphabetical order
        order = sorted(members, key=lambda x: x['name'], reverse=True)
        return order, True, "Reversed alphabetical order"
    
    elif twist_type == "random_skip":
        # Skip random person
        if len(members) > 1:
            random.shuffle(members)
            skipped = members.pop(random.randint(0, len(members)-1))
            return members, True, f"Skipped {skipped['name']}"
        return members, False, "Not enough members to skip"
    
    elif twist_type == "double_turn":
        # Someone goes twice
        random.shuffle(members)
        if members:
            lucky_person = random.choice(members)
            members.append(lucky_person)
            return members, True, f"{lucky_person['name']} goes twice!"
        return members, False, "No members available"
    
    elif twist_type == "pair_up":
        # Pair people up
        random.shuffle(members)
        pairs = []
        for i in range(0, len(members), 2):
            if i + 1 < len(members):
                pairs.append(f"{members[i]['name']} & {members[i+1]['name']}")
            else:
                pairs.append(members[i]['name'])
        # Convert back to member format for display
        paired_members = []
        for pair in pairs:
            paired_members.append({"name": pair, "emoji": "👥", "id": f"pair_{len(paired_members)}"})
        return paired_members, True, "Members paired up!"
    
    else:
        # No twist - just randomize
        random.shuffle(members)
        return members, False, "Random order (no twist)"

# Routes
@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
    <html>
        <head><title>Standup Spinner API</title></head>
        <body>
            <h1>Standup Spinner API</h1>
            <p>Your standup spinner backend is running!</p>
            <p><a href="/docs">View API Documentation</a></p>
        </body>
    </html>
    """

@app.post("/members/", response_class=HTMLResponse)
def create_member(name: str = Form(...), emoji: str = Form("👤"), db: Session = Depends(get_db)):
    """Add a new team member and return HTML for HTMX"""
    db_member = TeamMember(name=name, emoji=emoji)
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    
    # Return HTML for the new member checkbox
    return f"""
    <label class="flex items-center gap-3 p-3 bg-white rounded-xl border border-gray-200 hover:bg-gray-50 cursor-pointer">
        <input type="checkbox" name="member_ids" value="{db_member.id}" checked 
               class="w-5 h-5 text-blue-600 rounded focus:ring-blue-500">
        <span class="text-2xl">{db_member.emoji}</span>
        <span class="font-medium">{db_member.name}</span>
    </label>
    """

@app.get("/members/")
def get_members(request: Request, db: Session = Depends(get_db)):
    """Get all active team members - returns JSON for API calls, HTML for HTMX"""
    members = db.query(TeamMember).filter(TeamMember.is_active == True).all()
    
    # Check if request expects JSON (from JavaScript) or HTML (from HTMX)
    accept_header = request.headers.get("accept", "")
    if "application/json" in accept_header or "text/html" not in accept_header:
        # Return JSON for API calls
        return [
            {
                "id": member.id,
                "name": member.name,
                "emoji": member.emoji,
                "is_active": member.is_active
            }
            for member in members
        ]
    
    # Return HTML for HTMX calls
    html_parts = []
    for member in members:
        html_parts.append(f"""
        <label class="flex items-center gap-3 p-3 bg-white rounded-xl border border-gray-200 hover:bg-gray-50 cursor-pointer">
            <input type="checkbox" name="member_ids" value="{member.id}" checked
                   class="w-5 h-5 text-blue-600 rounded focus:ring-blue-500">
            <span class="text-2xl">{member.emoji}</span>
            <span class="font-medium">{member.name}</span>
        </label>
        """)
    
    return HTMLResponse("".join(html_parts))

@app.delete("/members/{member_id}")
def delete_member(member_id: int, db: Session = Depends(get_db)):
    """Deactivate a team member"""
    member = db.query(TeamMember).filter(TeamMember.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    member.is_active = False
    db.commit()
    return {"message": "Member deactivated"}

@app.post("/spin/")
def spin_standup(
    request: Request,
    member_ids: List[int] = Form(...),
    twist_type: str = Form("random"),
    db: Session = Depends(get_db)
):
    """Spin the standup wheel with a twist - returns JSON for API calls, HTML for HTMX"""
    # Get members
    members = db.query(TeamMember).filter(
        TeamMember.id.in_(member_ids),
        TeamMember.is_active == True
    ).all()

    if not members:
        raise HTTPException(status_code=400, detail="No valid members found")

    # Convert to dict for processing
    member_dicts = [
        {"id": m.id, "name": m.name, "emoji": m.emoji}
        for m in members
    ]

    # Apply twist and get order
    order, twist_applied, twist_description = apply_twist(member_dicts, twist_type)

    # Save to database
    session_id = str(random.randint(100000, 999999))
    for position, member_data in enumerate(order):
        spin_order = SpinOrder(
            session_id=session_id,
            member_id=member_data["id"],
            position=position + 1,
            twist_type=twist_type if twist_applied else "none"
        )
        db.add(spin_order)
    db.commit()

    # Check if request expects JSON (from JavaScript) or HTML (from HTMX)
    accept_header = request.headers.get("accept", "")
    if "application/json" in accept_header or "text/html" not in accept_header:
        # Return JSON for API calls
        return {
            "order": order,
            "twist_applied": twist_applied,
            "twist_description": twist_description,
            "session_id": session_id
        }

    # Return HTML for HTMX calls (keep the existing HTML generation code)
    html_parts = [f"""
    <div class="bg-gradient-to-r from-purple-400 to-pink-400 rounded-lg p-6 text-white">
        <h3 class="text-xl font-bold mb-4">🎉 Standup Order</h3>
        <div class="space-y-2">
    """]
    
    for i, member_data in enumerate(order):
        html_parts.append(f"""
            <div class="flex items-center space-x-3 bg-white bg-opacity-20 rounded-lg p-3">
                <span class="text-2xl font-bold">{i + 1}</span>
                <span class="text-xl">{member_data['emoji'] or '👤'}</span>
                <span class="text-lg font-medium">{member_data['name']}</span>
            </div>
        """)
    
    html_parts.append("</div>")
    
    if twist_applied:
        html_parts.append(f"""
            <div class="mt-4 bg-yellow-400 bg-opacity-30 rounded-lg p-3">
                <span class="text-sm font-medium">✨ Twist Applied: {twist_description}</span>
            </div>
        """)
    
    html_parts.append("</div>")
    
    return HTMLResponse("".join(html_parts))

@app.get("/stats/", response_class=HTMLResponse)
def get_stats(days: int = 30, db: Session = Depends(get_db)):
    """Get standup statistics as HTML for HTMX"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Get all orders from the specified period
    orders = db.query(StandupOrder).filter(
        StandupOrder.timestamp >= cutoff_date
    ).all()
    
    if not orders:
        return '<div class="text-center text-gray-500 py-12"><p>No standup data available yet.</p></div>'
    
    # Calculate stats per member
    member_stats = {}
    session_sizes = {}
    
    # First, get session sizes
    for order in orders:
        if order.session_id not in session_sizes:
            session_orders = [o for o in orders if o.session_id == order.session_id]
            session_sizes[order.session_id] = len(session_orders)
    
    # Calculate member statistics
    for order in orders:
        member_id = order.member_id
        member_name = order.member_name
        
        if member_id not in member_stats:
            # Get member emoji
            member = db.query(TeamMember).filter(TeamMember.id == member_id).first()
            emoji = member.emoji if member else "👤"
            
            member_stats[member_id] = {
                "member_name": member_name,
                "emoji": emoji,
                "first_count": 0,
                "last_count": 0,
                "total_standups": 0,
                "positions": []
            }
        
        stats = member_stats[member_id]
        stats["total_standups"] += 1
        stats["positions"].append(order.order_position)
        
        # Check if first or last
        session_size = session_sizes[order.session_id]
        if order.order_position == 1:
            stats["first_count"] += 1
        elif order.order_position == session_size:
            stats["last_count"] += 1
    
    # Generate HTML response
    html_parts = []
    for member_id, stats in sorted(member_stats.items(), key=lambda x: x[1]["total_standups"], reverse=True):
        avg_position = sum(stats["positions"]) / len(stats["positions"])
        
        html_parts.append(f"""
        <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-200 text-center hover:shadow-md transition-shadow">
            <div class="text-3xl mb-3">{stats['emoji']}</div>
            <h4 class="font-bold text-gray-800 mb-3">{stats['member_name']}</h4>
            <div class="grid grid-cols-2 gap-4 text-sm">
                <div>
                    <div class="text-2xl font-bold text-green-600">{stats['first_count']}</div>
                    <div class="text-gray-600">First</div>
                </div>
                <div>
                    <div class="text-2xl font-bold text-red-600">{stats['last_count']}</div>
                    <div class="text-gray-600">Last</div>
                </div>
                <div>
                    <div class="text-2xl font-bold text-blue-600">{stats['total_standups']}</div>
                    <div class="text-gray-600">Total</div>
                </div>
                <div>
                    <div class="text-2xl font-bold text-purple-600">{avg_position:.1f}</div>
                    <div class="text-gray-600">Avg Pos</div>
                </div>
            </div>
        </div>
        """)
    
    return "".join(html_parts)
    
    # First, get session sizes
    for order in orders:
        if order.session_id not in session_sizes:
            session_orders = [o for o in orders if o.session_id == order.session_id]
            session_sizes[order.session_id] = len(session_orders)
    
    # Calculate member statistics
    for order in orders:
        member_id = order.member_id
        member_name = order.member_name
        
        if member_id not in member_stats:
            # Get member emoji
            member = db.query(TeamMember).filter(TeamMember.id == member_id).first()
            emoji = member.emoji if member else "👤"
            
            member_stats[member_id] = {
                "member_name": member_name,
                "emoji": emoji,
                "first_count": 0,
                "last_count": 0,
                "total_standups": 0,
                "positions": []
            }
        
        stats = member_stats[member_id]
        stats["total_standups"] += 1
        stats["positions"].append(order.order_position)
        
        # Check if first or last
        session_size = session_sizes[order.session_id]
        if order.order_position == 1:
            stats["first_count"] += 1
        elif order.order_position == session_size:
            stats["last_count"] += 1
    
    # Calculate averages and format response
    result = []
    for member_id, stats in member_stats.items():
        avg_position = sum(stats["positions"]) / len(stats["positions"])
        
        result.append(StatsResponse(
            member_name=stats["member_name"],
            emoji=stats["emoji"],
            first_count=stats["first_count"],
            last_count=stats["last_count"],
            total_standups=stats["total_standups"],
            avg_position=round(avg_position, 2)
        ))
    
    # Sort by total standups
    result.sort(key=lambda x: x.total_standups, reverse=True)
    return result

@app.get("/twists/")
def get_available_twists():
    """Get available twist types"""
    return {
        "twists": [
            {"id": "random", "name": "🎲 Random Shuffle", "description": "Completely random order"},
            {"id": "reverse", "name": "🔄 Reverse Alpha", "description": "Reverse alphabetical order"},
            {"id": "skip_one", "name": "⏭️ Skip Pattern", "description": "Every other person pattern"},
            {"id": "emoji_sort", "name": "😊 Emoji Sort", "description": "Sort by emoji"},
            {"id": "length_sort", "name": "📏 Name Length", "description": "Sort by name length"}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
