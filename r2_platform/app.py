import os
import re
import math
import time
import base64
import hashlib
import datetime
import sqlite3
import joblib
from functools import wraps
from flask import (
    Flask, request, jsonify, render_template,
    session, send_from_directory, redirect, url_for
)
from werkzeug.security import generate_password_hash, check_password_hash

# -------------------------------------------------------------
# Configuration & Setup
# -------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "emergency_r2.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
MODEL_PATH = os.path.join(BASE_DIR, "model.joblib")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = "crisisguard_hackathon_super_secret_key_r2"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16 MB

# Load ML Severity Pipeline if available
ml_pipeline = None
if os.path.exists(MODEL_PATH):
    try:
        ml_pipeline = joblib.load(MODEL_PATH)
        print("Loaded ML Severity Model successfully.")
    except Exception as e:
        print("Warning: Could not load model.joblib:", e)

# -------------------------------------------------------------
# Database Helpers
# -------------------------------------------------------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    # Users / Auth (Admin and Responders)
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL, -- 'admin' or 'responder'
        responder_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Responders Table (Ambulance, Fire Engine, Police)
    c.execute('''
    CREATE TABLE IF NOT EXISTS responders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        unit_type TEXT NOT NULL, -- 'Ambulance', 'Fire Engine', 'Police'
        station_name TEXT NOT NULL,
        lat REAL NOT NULL,
        lng REAL NOT NULL,
        phone TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Available', -- 'Available', 'Busy', 'Offline'
        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Incidents / Reports Table
    c.execute('''
    CREATE TABLE IF NOT EXISTS incidents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        category TEXT NOT NULL,
        lat REAL NOT NULL,
        lng REAL NOT NULL,
        landmark TEXT,
        location_source TEXT NOT NULL DEFAULT 'gps', -- 'gps' or 'pinned'
        people_affected INTEGER NOT NULL DEFAULT 0,
        contact_info TEXT,
        language TEXT NOT NULL DEFAULT 'en', -- 'en', 'ta', 'tanglish'
        
        -- Severity Breakdown
        rule_severity TEXT NOT NULL,
        ai_severity TEXT NOT NULL,
        final_severity TEXT NOT NULL,
        
        -- Credibility
        trust_score INTEGER NOT NULL DEFAULT 100,
        trust_label TEXT NOT NULL,
        trust_flags TEXT,
        
        -- Photo Evidence
        photo_filename TEXT,
        photo_hash TEXT,
        photo_timestamp INTEGER,
        
        -- Status Lifecycle: Reported -> Assigned -> In Progress -> Resolved (or Verified, Fake)
        status TEXT NOT NULL DEFAULT 'Reported',
        priority_rank REAL DEFAULT 0,
        
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Dispatches Table (Zomato/Swiggy first-accept-wins mechanic)
    c.execute('''
    CREATE TABLE IF NOT EXISTS dispatches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        incident_id INTEGER NOT NULL,
        unit_type TEXT NOT NULL, -- 'Ambulance', 'Fire Engine', 'Police'
        status TEXT NOT NULL DEFAULT 'Open', -- 'Open', 'Claimed', 'En Route', 'Arrived', 'Completed', 'Expired'
        claimed_by INTEGER, -- responder_id
        claimed_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (incident_id) REFERENCES incidents (id),
        FOREIGN KEY (claimed_by) REFERENCES responders (id)
    )
    ''')

    # Dispatch Alerts Table (Per responder delivered alert & radius expansion)
    c.execute('''
    CREATE TABLE IF NOT EXISTS dispatch_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dispatch_id INTEGER NOT NULL,
        responder_id INTEGER NOT NULL,
        distance_km REAL NOT NULL,
        delivered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        seen_at TIMESTAMP,
        FOREIGN KEY (dispatch_id) REFERENCES dispatches (id),
        FOREIGN KEY (responder_id) REFERENCES responders (id)
    )
    ''')

    # Audit Trail for dispatch events
    c.execute('''
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        incident_id INTEGER,
        dispatch_id INTEGER,
        actor TEXT,
        action TEXT NOT NULL,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    conn.commit()
    conn.close()

# -------------------------------------------------------------
# Seeding Demo Responders & Accounts (Chennai / Chengalpattu Hub)
# -------------------------------------------------------------
def seed_demo_data():
    conn = get_db()
    c = conn.cursor()

    # Seed 5 specific demo responders: 3 Ambulances, 2 Fire Engines
    # Format: (username, name, vehicle_label, unit_type, station_name, lat, lng, phone, initial_status)
    demo_responders = [
        ("amb01", "Karthik Rajan", "Ambulance 01", "Ambulance", "Apollo Greams Road, Thousand Lights", 13.0560, 80.2520, "+91 98401 11201", "Available"),
        ("amb02", "Praveen Kumar", "Ambulance 02", "Ambulance", "RGGGH Central Hospital, Chennai", 13.0784, 80.2785, "+91 98401 11202", "Available"),
        ("amb03", "Senthil Nathan", "Ambulance 03", "Ambulance", "MIOT International, Manapakkam", 13.0182, 80.1873, "+91 98401 11203", "Available"),
        ("fe01", "Murugan Selvam", "Fire Engine 01", "Fire Engine", "Kilpauk Fire Station, Chennai", 13.0805, 80.2415, "+91 94450 86101", "Available"),
        ("fe02", "Venkatesh Babu", "Fire Engine 02", "Fire Engine", "Guindy Industrial Estate Fire Station", 13.0067, 80.2088, "+91 94450 86102", "Available"),
    ]

    for uname, driver_name, veh_label, u_type, station, lat, lng, phone, st in demo_responders:
        full_display_name = f"{driver_name} ({veh_label})"
        c.execute("SELECT id FROM responders WHERE phone = ?", (phone,))
        existing = c.fetchone()
        if existing:
            resp_id = existing[0]
            c.execute('''
            UPDATE responders SET name = ?, unit_type = ?, station_name = ?, lat = ?, lng = ? WHERE id = ?
            ''', (full_display_name, u_type, station, lat, lng, resp_id))
        else:
            c.execute('''
            INSERT INTO responders (name, unit_type, station_name, lat, lng, phone, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (full_display_name, u_type, station, lat, lng, phone, st))
            resp_id = c.lastrowid

        # Upsert user account (password: responder123)
        pwd_hash = generate_password_hash("responder123")
        c.execute("SELECT id FROM users WHERE username = ?", (uname,))
        user_row = c.fetchone()
        if user_row:
            c.execute("UPDATE users SET password_hash = ?, responder_id = ? WHERE id = ?", (pwd_hash, resp_id, user_row[0]))
        else:
            c.execute('''
            INSERT INTO users (username, password_hash, role, responder_id)
            VALUES (?, ?, 'responder', ?)
            ''', (uname, pwd_hash, resp_id))

    # Admin user (admin / admin123)
    admin_pwd = generate_password_hash("admin123")
    c.execute("SELECT id FROM users WHERE username = 'admin'")
    admin_row = c.fetchone()
    if admin_row:
        c.execute("UPDATE users SET password_hash = ? WHERE id = ?", (admin_pwd, admin_row[0]))
    else:
        c.execute('''
        INSERT INTO users (username, password_hash, role, responder_id)
        VALUES ('admin', ?, 'admin', NULL)
        ''', (admin_pwd,))

    conn.commit()
    conn.close()
    print("Idempotently seeded 5 demo responder accounts (amb01..03, fe01..02 / responder123) and admin.")
# -------------------------------------------------------------
# Requirement 1: Multilingual Detection & Automated Severity
# -------------------------------------------------------------
TANGLISH_KEYWORDS = {
    'thee', 'neruppu', 'kapathunga', 'kaapathunga', 'seekiram', 'seekram',
    'veedu', 'kattidam', 'collapse', 'ratham', 'adi', 'vithuram', 'mudila',
    'thanni', 'vellam', 'valikidhu', 'valikuthu', 'aabathu', 'uyir', 'kaayal',
    'accident', 'ambulans', 'loosu', 'vanthuduchi', 'maatikichi', 'maatikitanga',
    'poranga', 'romba', 'periya', 'chinna', 'saavu', 'maranam', 'nenju', 'vali',
    'moochu', 'faint', 'thirudan', 'adichu', 'kollai'
}

def detect_language(text: str) -> str:
    """
    Auto-detect language:
    - Tamil Unicode range \u0B80-\u0BFF = Tamil ('ta')
    - Matches known Tanglish vocabulary = Tanglish ('tanglish')
    - Otherwise English ('en')
    """
    if not text:
        return 'en'
    
    # Check for Tamil script
    if re.search(r'[\u0B80-\u0BFF]', text):
        return 'ta'
    
    # Check for Tanglish words in lower text
    tokens = set(re.findall(r'[a-zA-Z]+', text.lower()))
    intersection = tokens.intersection(TANGLISH_KEYWORDS)
    if len(intersection) >= 1:
        return 'tanglish'
    
    return 'en'

SEVERITY_LEVELS = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}
LEVEL_NAMES = {1: "Low", 2: "Medium", 3: "High", 4: "Critical"}

def compute_rule_severity(category: str, people_affected: int, description: str) -> str:
    cat = (category or "").lower()
    count = max(0, people_affected or 0)
    desc = (description or "").lower()

    # Danger keywords across English, Tamil, and Tanglish
    critical_keywords = [
        # English
        'collapse', 'trapped', 'explosion', 'fireball', 'dead', 'fatalities', 'submerged',
        'suffocating', 'unresponsive', 'unconscious', 'severe burns',
        # Tamil
        'இடிந்து', 'சிக்கியுள்ளனர்', 'வெடிவிபத்து', 'உயிரிழப்பு', 'மூழ்கியது', 'உயிருக்கு ஆபத்து',
        # Tanglish
        'maatikitanga', 'maatikichi', 'collapse', 'blast', 'unconscious', 'dead', 'ratham'
    ]

    has_danger_kw = any(kw in desc for kw in critical_keywords)

    score = 1 # Low
    if cat in ['building collapse', 'flood', 'fire emergency']:
        score = 2 # Starts at Medium
        if count >= 3 or has_danger_kw:
            score = 4 # Critical
        elif count >= 1:
            score = 3 # High
    elif cat in ['road accident', 'medical emergency']:
        score = 1
        if count >= 5 or (count >= 2 and has_danger_kw):
            score = 4
        elif count >= 2 or has_danger_kw:
            score = 3
        elif count == 1:
            score = 2
    else: # Other
        if count >= 5:
            score = 3
        elif count >= 2:
            score = 2

    # Mass casualty override
    if count >= 10:
        score = 4

    return LEVEL_NAMES[score]

def predict_ai_severity(text: str) -> str:
    if ml_pipeline:
        try:
            pred = ml_pipeline.predict([text])[0]
            if pred in SEVERITY_LEVELS:
                return pred
        except Exception as e:
            print("ML Prediction error:", e)
    return "Medium"

def evaluate_final_severity(category: str, people_affected: int, description: str):
    rule_sev = compute_rule_severity(category, people_affected, description)
    ai_sev = predict_ai_severity(description)

    # Final severity = HIGHER of (rule_based, ML prediction) to guarantee never under-triaging
    final_score = max(SEVERITY_LEVELS.get(rule_sev, 1), SEVERITY_LEVELS.get(ai_sev, 1))
    final_sev = LEVEL_NAMES[final_score]

    return rule_sev, ai_sev, final_sev

# -------------------------------------------------------------
# Haversine Distance Helper
# -------------------------------------------------------------
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0 # Earth's radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

# -------------------------------------------------------------
# Requirement 2 & Dynamic Priority Rank Engine
# -------------------------------------------------------------
def calculate_priority_rank(incident_row) -> float:
    """
    Ranks active incidents dynamically based on:
    Severity Level + Number of People Affected + Time Elapsed Since Reporting + Category Hazard Level
    """
    sev_weights = {"Critical": 100.0, "High": 60.0, "Medium": 30.0, "Low": 10.0}
    cat_weights = {
        "Building Collapse": 30.0,
        "Fire Emergency": 25.0,
        "Flood": 22.0,
        "Road Accident": 18.0,
        "Medical Emergency": 18.0,
        "Other": 10.0
    }

    base_sev = sev_weights.get(incident_row['final_severity'], 10.0)
    cat_val = cat_weights.get(incident_row['category'], 10.0)
    people_val = min(50.0, float(incident_row['people_affected'] or 0) * 4.0)

    # Time elapsed in minutes (older waiting incidents gain priority)
    time_elapsed_min = 0.0
    try:
        created = datetime.datetime.fromisoformat(incident_row['created_at'])
        diff = (datetime.datetime.utcnow() - created).total_seconds() / 60.0
        time_elapsed_min = min(40.0, max(0.0, diff * 1.5))
    except Exception:
        pass

    return round(base_sev + cat_val + people_val + time_elapsed_min, 2)

# -------------------------------------------------------------
# Requirement 3: Credibility & Live Photo Evaluation
# -------------------------------------------------------------
GIBBERISH_PATTERN = re.compile(r'^(asdf|qwerty|1234|test|fake|bla|xyz)+$', re.I)

def evaluate_credibility(data, client_ip, existing_db_conn):
    score = 100
    flags = []

    title = (data.get('title') or "").strip()
    desc = (data.get('description') or "").strip()
    cat = data.get('category')
    contact = (data.get('contact_info') or "").strip()
    people = int(data.get('people_affected') or 0)
    honeypot = (data.get('website_check') or "").strip() # Honeypot hidden input
    lat = float(data.get('lat') or 0.0)
    lng = float(data.get('lng') or 0.0)
    loc_source = data.get('location_source') or 'gps'
    photo_ts = int(data.get('photo_timestamp') or 0)
    photo_hash = data.get('photo_hash') or ""
    gps_lat = data.get('device_gps_lat')
    gps_lng = data.get('device_gps_lng')

    # 1. Honeypot filled by bot
    if honeypot:
        score -= 50
        flags.append("Bot activity: Honeypot field was filled")

    # 2. Text too short or gibberish
    if len(desc) < 8 or len(title) < 4:
        score -= 25
        flags.append("Description or title is excessively short")
    if GIBBERISH_PATTERN.search(title) or GIBBERISH_PATTERN.search(desc):
        score -= 30
        flags.append("Suspected gibberish / keystroke spamming")

    # 3. Unrealistic casualty count
    if people > 1000:
        score -= 25
        flags.append(f"Unrealistic people affected count ({people})")

    # 4. Check photo freshness (must be live captured within last 10 minutes)
    now_ts = int(time.time() * 1000)
    if photo_ts > 0:
        age_minutes = (now_ts - photo_ts) / 60000.0
        if age_minutes > 10:
            score -= 20
            flags.append(f"Stale camera frame ({age_minutes:.1f} mins old)")
    else:
        score -= 15
        flags.append("Missing live camera timestamp")

    # 5. Reused photo hash check in database
    c = existing_db_conn.cursor()
    c.execute("SELECT id FROM incidents WHERE photo_hash = ? LIMIT 1", (photo_hash,))
    reused = c.fetchone()
    if reused:
        score -= 35
        flags.append(f"Duplicate photo hash matching existing incident #{reused[0]}")

    # 6. Duplicate report check (same category & within 500m within last 30 minutes)
    c.execute('''
    SELECT id, lat, lng FROM incidents 
    WHERE category = ? AND datetime(created_at) >= datetime('now', '-30 minutes')
    ''', (cat,))
    for row in c.fetchall():
        d = haversine_km(lat, lng, row['lat'], row['lng'])
        if d < 0.5:
            flags.append(f"Corroborating report near Incident #{row['id']} ({d*1000:.0f}m away)")
            # Notice: Corroboration actually validates the emergency rather than penalizes!
            score = min(100, score + 5)
            break

    # 7. Pin distance from user's live device GPS
    if loc_source == "pinned" and gps_lat and gps_lng:
        try:
            pin_dist = haversine_km(float(gps_lat), float(gps_lng), lat, lng)
            if pin_dist > 1.0:
                flags.append(f"Pin placed {pin_dist:.1f}km away from device GPS position")
                score -= 10
        except Exception:
            pass

    score = max(10, min(100, score))
    if score >= 75:
        label = "Looks Genuine"
    elif score >= 45:
        label = "Needs Review"
    else:
        label = "Suspicious"

    return score, label, "; ".join(flags) if flags else "No anomalies detected"

# -------------------------------------------------------------
# Requirement 4: Zomato/Swiggy-Style Dispatch Router
# -------------------------------------------------------------
def determine_required_units(category: str, people_affected: int, description: str):
    """
    Category -> Agencies:
    Fire Emergency -> Fire Engine (+ Ambulance if people_affected > 0 or danger keywords)
    Road Accident -> Ambulance + Police
    Medical Emergency -> Ambulance
    Flood -> Fire Engine (Rescue) + Police
    Building Collapse -> Fire Engine + Ambulance + Police
    Other -> Police
    """
    cat = (category or "").lower()
    desc = (description or "").lower()
    units = set()

    if cat == "fire emergency":
        units.add("Fire Engine")
        if people_affected > 0 or any(w in desc for w in ['burn', 'injured', 'smoke', 'hospital', 'casualty', 'ratham', 'thee']):
            units.add("Ambulance")
    elif cat == "road accident":
        units.add("Ambulance")
        units.add("Police")
    elif cat == "medical emergency":
        units.add("Ambulance")
    elif cat == "flood":
        units.add("Fire Engine")
        units.add("Police")
    elif cat == "building collapse":
        units.add("Fire Engine")
        units.add("Ambulance")
        units.add("Police")
    else:
        units.add("Police")

    return list(units)

def trigger_dispatches_for_incident(incident_id: int, db_conn, radius_km: float = 25.0):
    """
    Computes haversine distance to available responders and creates dispatch alert broadcasts.
    Returns the integer count of available responders actually notified.
    """
    c = db_conn.cursor()
    c.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
    inc = c.fetchone()
    if not inc:
        return 0

    required_units = determine_required_units(inc['category'], inc['people_affected'], inc['description'])
    total_alerts_sent = 0

    for unit_type in required_units:
        # Check if an open/claimed dispatch for this unit already exists for this incident
        c.execute('''
        SELECT id, status FROM dispatches 
        WHERE incident_id = ? AND unit_type = ? AND status IN ('Open', 'Claimed', 'En Route', 'Arrived')
        ''', (incident_id, unit_type))
        existing_dispatch = c.fetchone()
        
        if existing_dispatch:
            dispatch_id = existing_dispatch['id']
        else:
            c.execute('''
            INSERT INTO dispatches (incident_id, unit_type, status)
            VALUES (?, ?, 'Open')
            ''', (incident_id, unit_type))
            dispatch_id = c.lastrowid

            # Log audit
            c.execute('''
            INSERT INTO audit_logs (incident_id, dispatch_id, actor, action, details)
            VALUES (?, ?, 'SYSTEM', 'DISPATCH_BROADCAST_CREATED', ?)
            ''', (incident_id, dispatch_id, f"Broadcast open for {unit_type} units within {radius_km}km"))

        # Broadcast to all matching Available responders within radius
        c.execute('''
        SELECT id, lat, lng FROM responders 
        WHERE unit_type = ? AND status = 'Available'
        ''', (unit_type,))
        for resp in c.fetchall():
            dist = haversine_km(inc['lat'], inc['lng'], resp['lat'], resp['lng'])
            if dist <= radius_km:
                c.execute('''
                INSERT OR IGNORE INTO dispatch_alerts (dispatch_id, responder_id, distance_km)
                VALUES (?, ?, ?)
                ''', (dispatch_id, resp['id'], dist))
                total_alerts_sent += 1

    db_conn.commit()
    return total_alerts_sent
# -------------------------------------------------------------
# Security & Auth Decorators
# -------------------------------------------------------------
def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({"error": "Authentication required"}), 401
            if role and session.get('role') != role:
                return jsonify({"error": "Forbidden: insufficient permissions"}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# -------------------------------------------------------------
# API Endpoints
# -------------------------------------------------------------

# 1. Auth APIs
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    username = (data.get('username') or "").strip()
    password = (data.get('password') or "").strip()

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()

    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({"error": "Invalid username or password"}), 401

    session['user_id'] = user['id']
    session['username'] = user['username']
    session['role'] = user['role']
    session['responder_id'] = user['responder_id']

    return jsonify({
        "message": "Login successful",
        "user": {
            "id": user['id'],
            "username": user['username'],
            "role": user['role'],
            "responder_id": user['responder_id']
        }
    })

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"})

@app.route('/api/me', methods=['GET'])
def api_me():
    if 'user_id' not in session:
        return jsonify({"authenticated": False}), 200
    
    conn = get_db()
    c = conn.cursor()
    responder = None
    if session.get('responder_id'):
        c.execute("SELECT * FROM responders WHERE id = ?", (session['responder_id'],))
        r = c.fetchone()
        if r:
            responder = dict(r)
    conn.close()

    return jsonify({
        "authenticated": True,
        "user_id": session.get('user_id'),
        "username": session.get('username'),
        "role": session.get('role'),
        "responder": responder
    })

# 2. Citizen Report Submission (Requirement 1, 3, 4)
@app.route('/api/reports', methods=['POST'])
def submit_report():
    data = request.get_json() or {}
    title = (data.get('title') or "").strip()
    desc = (data.get('description') or "").strip()
    category = data.get('category') or "Other"
    lat = float(data.get('lat') or 13.0827)
    lng = float(data.get('lng') or 80.2707)
    landmark = (data.get('landmark') or "").strip()
    loc_source = data.get('location_source') or "gps"
    people_affected = int(data.get('people_affected') or 0)
    contact_info = (data.get('contact_info') or "").strip()
    photo_b64 = data.get('photo_base64') or ""
    photo_ts = int(data.get('photo_timestamp') or 0)

    if not title or not desc:
        return jsonify({"error": "Title and description are required"}), 400

    # Validate Photo (Optional in Step 4)
    photo_filename = None
    photo_hash = None
    if photo_b64:
        try:
            clean_b64 = photo_b64.split("base64,")[1] if "base64," in photo_b64 else photo_b64
            photo_bytes = base64.b64decode(clean_b64)
            photo_hash = hashlib.sha256(photo_bytes).hexdigest()
            photo_filename = f"incident_{int(time.time())}_{photo_hash[:8]}.jpg"
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_filename)
            with open(photo_path, "wb") as f:
                f.write(photo_bytes)
        except Exception as e:
            print("Warning: Photo decode skipped:", e)

    # Language Detection (Requirement 1)
    lang = detect_language(f"{title} {desc}")

    # Multilingual Severity Evaluation (Rule + ML Pipeline)
    rule_sev, ai_sev, final_sev = evaluate_final_severity(category, people_affected, desc)

    conn = get_db()
    c = conn.cursor()

    # Credibility Scoring & Anti-Fake Engine (Requirement 3)
    data['photo_hash'] = photo_hash
    trust_score, trust_label, trust_flags = evaluate_credibility(data, request.remote_addr, conn)

    # Initial status
    # Low-trust reports (<45%) go to Needs Verification unless Critical
    initial_status = "Reported"
    if trust_score < 45 and final_sev != "Critical":
        initial_status = "Needs Verification"

    c.execute('''
    INSERT INTO incidents (
        title, description, category, lat, lng, landmark, location_source,
        people_affected, contact_info, language, rule_severity, ai_severity,
        final_severity, trust_score, trust_label, trust_flags,
        photo_filename, photo_hash, photo_timestamp, status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        title, desc, category, lat, lng, landmark, loc_source,
        people_affected, contact_info, lang, rule_sev, ai_sev,
        final_sev, trust_score, trust_label, trust_flags,
        photo_filename, photo_hash, photo_ts, initial_status
    ))
    incident_id = c.lastrowid

    # Compute Priority Rank
    c.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
    inc_row = c.fetchone()
    p_rank = calculate_priority_rank(inc_row)
    c.execute("UPDATE incidents SET priority_rank = ? WHERE id = ?", (p_rank, incident_id))

    # Audit log
    c.execute('''
    INSERT INTO audit_logs (incident_id, actor, action, details)
    VALUES (?, 'CITIZEN', 'INCIDENT_SUBMITTED', ?)
    ''', (incident_id, f"Reported {final_sev} severity in language '{lang}'. Trust: {trust_score}% ({trust_label})"))

    conn.commit()

    # Trigger Zomato/Swiggy-style Dispatch Alerts immediately if not held for verification
    alerts_sent_count = 0
    if initial_status != "Needs Verification":
        alerts_sent_count = trigger_dispatches_for_incident(incident_id, conn)

    # Format tracking code RQ-XXXX
    tracking_code = f"RQ-{incident_id:04d}"

    conn.close()

    return jsonify({
        "success": True,
        "incident_id": incident_id,
        "tracking_code": tracking_code,
        "alerts_sent": alerts_sent_count,
        "language": lang,
        "rule_severity": rule_sev,
        "ai_severity": ai_sev,
        "final_severity": final_sev,
        "trust_score": trust_score,
        "trust_label": trust_label,
        "status": initial_status,
        "message": "Emergency incident registered and dispatched successfully"
    }), 201

# 3. Citizen Live Tracking Screen API
@app.route('/api/track/<int:incident_id>', methods=['GET'])
def track_incident(incident_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
    inc = c.fetchone()
    if not inc:
        conn.close()
        return jsonify({"error": "Incident not found"}), 404

    # Fetch dispatches and claimed responder info
    c.execute('''
    SELECT d.*, r.name as responder_name, r.unit_type, r.phone as responder_phone,
           r.lat as responder_lat, r.lng as responder_lng, r.station_name
    FROM dispatches d
    LEFT JOIN responders r ON d.claimed_by = r.id
    WHERE d.incident_id = ?
    ''', (incident_id,))
    dispatches = [dict(row) for row in c.fetchall()]

    conn.close()

    # Calculate ETA based on responder distance
    for d in dispatches:
        if d.get('responder_lat') and d.get('responder_lng'):
            dist = haversine_km(inc['lat'], inc['lng'], d['responder_lat'], d['responder_lng'])
            d['distance_km'] = dist
            # Avg speed 40 km/h with siren -> minutes = dist / 40 * 60 + 2 min buffer
            d['eta_minutes'] = max(2, int((dist / 40.0) * 60.0) + 2)

    # Compute total alerts sent across all dispatches for this incident
    c = get_db().cursor()
    c.execute('''
    SELECT COUNT(DISTINCT responder_id) FROM dispatch_alerts 
    WHERE dispatch_id IN (SELECT id FROM dispatches WHERE incident_id = ?)
    ''', (incident_id,))
    alerts_sent_count = c.fetchone()[0]

    return jsonify({
        "incident": dict(inc),
        "dispatches": dispatches,
        "alerts_sent": alerts_sent_count,
        "tracking_code": f"RQ-{incident_id:04d}"
    })

# 4. Admin Reports & Incidents Management APIs
@app.route('/api/reports', methods=['GET'])
def get_reports():
    conn = get_db()
    c = conn.cursor()
    
    # Update priority ranks dynamically for all active incidents
    c.execute("SELECT * FROM incidents ORDER BY id DESC")
    rows = c.fetchall()
    
    incidents_list = []
    for r in rows:
        d = dict(r)
        d['priority_rank'] = calculate_priority_rank(r)
        incidents_list.append(d)

    # Sort priority: Open/Active first, then highest priority_rank desc
    def sort_key(item):
        is_open = 1 if item['status'] not in ('Resolved', 'Fake/Duplicate') else 0
        return (is_open, item['priority_rank'], item['id'])

    incidents_list.sort(key=sort_key, reverse=True)

    # Also fetch all active dispatches
    c.execute('''
    SELECT d.*, r.name as responder_name, r.lat as responder_lat, r.lng as responder_lng, r.phone
    FROM dispatches d
    LEFT JOIN responders r ON d.claimed_by = r.id
    ''')
    dispatches = [dict(row) for row in c.fetchall()]

    conn.close()
    return jsonify({
        "incidents": incidents_list,
        "dispatches": dispatches
    })

@app.route('/api/reports/<int:incident_id>', methods=['PATCH'])
def update_report(incident_id):
    data = request.get_json() or {}
    new_status = data.get('status')

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
    inc = c.fetchone()
    if not inc:
        conn.close()
        return jsonify({"error": "Incident not found"}), 404

    actor = session.get('username') or 'ADMIN'

    if new_status:
        c.execute("UPDATE incidents SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_status, incident_id))
        c.execute('''
        INSERT INTO audit_logs (incident_id, actor, action, details)
        VALUES (?, ?, 'STATUS_UPDATE', ?)
        ''', (incident_id, actor, f"Status updated to '{new_status}'"))

        # If incident marked as Resolved or Fake, release all claimed responders
        if new_status in ('Resolved', 'Fake/Duplicate'):
            c.execute("SELECT claimed_by FROM dispatches WHERE incident_id = ? AND claimed_by IS NOT NULL", (incident_id,))
            claimed_responders = [row[0] for row in c.fetchall()]
            for r_id in claimed_responders:
                c.execute("UPDATE responders SET status = 'Available' WHERE id = ?", (r_id,))
            c.execute("UPDATE dispatches SET status = 'Completed' WHERE incident_id = ? AND status != 'Completed'", (incident_id,))

        # If acknowledged or verified from Needs Verification, trigger dispatch alerts
        if inc['status'] == "Needs Verification" and new_status == "Reported":
            trigger_dispatches_for_incident(incident_id, conn)

    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": f"Incident #{incident_id} updated"})

@app.route('/api/reports/<int:incident_id>', methods=['DELETE'])
def delete_report(incident_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM dispatch_alerts WHERE dispatch_id IN (SELECT id FROM dispatches WHERE incident_id = ?)", (incident_id,))
    c.execute("DELETE FROM dispatches WHERE incident_id = ?", (incident_id,))
    c.execute("DELETE FROM audit_logs WHERE incident_id = ?", (incident_id,))
    c.execute("DELETE FROM incidents WHERE id = ?", (incident_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": f"Incident #{incident_id} deleted"})

# 5. Requirement 4: Responder App & Zomato/Swiggy First-Accept-Wins Mechanic
@app.route('/api/responder/alerts', methods=['GET'])
def get_responder_alerts():
    responder_id = session.get('responder_id')
    if not responder_id:
        # Default to responder 1 for quick demo testing if not logged in
        responder_id = request.args.get('responder_id', 1, type=int)

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM responders WHERE id = ?", (responder_id,))
    resp = c.fetchone()
    if not resp:
        conn.close()
        return jsonify({"error": "Responder not found"}), 404

    # Fetch all dispatches matching responder's unit_type
    # Either Open (broadcasted) OR already claimed by this responder
    c.execute('''
    SELECT 
        d.id as dispatch_id, d.unit_type, d.status as dispatch_status, d.claimed_by, d.claimed_at,
        i.id as incident_id, i.title, i.description, i.category, i.lat, i.lng, i.landmark,
        i.final_severity, i.people_affected, i.language, i.trust_score, i.trust_label,
        i.photo_filename, i.created_at as incident_created_at,
        r_claimed.name as claimed_by_name
    FROM dispatches d
    JOIN incidents i ON d.incident_id = i.id
    LEFT JOIN responders r_claimed ON d.claimed_by = r_claimed.id
    WHERE d.unit_type = ? AND i.status NOT IN ('Resolved', 'Fake/Duplicate')
    ORDER BY d.id DESC
    ''', (resp['unit_type'],))

    alerts = []
    for row in c.fetchall():
        item = dict(row)
        dist = haversine_km(resp['lat'], resp['lng'], item['lat'], item['lng'])
        item['distance_km'] = dist
        item['is_claimed_by_me'] = (item['claimed_by'] == resp['id'])
        item['eta_minutes'] = max(2, int((dist / 40.0) * 60.0) + 2)
        alerts.append(item)

    # Sort alerts: Claimed by me first, then by distance ascending
    alerts.sort(key=lambda x: (not x['is_claimed_by_me'], x['distance_km']))

    conn.close()
    return jsonify({
        "responder": dict(resp),
        "alerts": alerts
    })

@app.route('/api/responder/dispatch/<int:dispatch_id>/accept', methods=['POST'])
def accept_dispatch(dispatch_id):
    """
    ATOMIC FIRST-ACCEPT-WINS MECHANIC WITH 1-ACTIVE-TASK SERVER ENFORCEMENT:
    1. Verify driver has NO active uncompleted tasks (returns 409 if active).
    2. Atomic SQL Update: UPDATE dispatches SET status='Claimed' WHERE id=? AND status='Open'.
    Only the first request succeeds; subsequent concurrent requests receive 409 Conflict.
    """
    req_data = request.get_json(silent=True) or {}
    responder_id = session.get('responder_id') or req_data.get('responder_id') or 1

    conn = get_db()
    c = conn.cursor()

    # Rule 4: Server Enforcement - A driver with a task that is not Completed must NOT be able to accept another
    c.execute('''
    SELECT id, incident_id, status FROM dispatches 
    WHERE claimed_by = ? AND status IN ('Claimed', 'En Route', 'Arrived')
    LIMIT 1
    ''', (responder_id,))
    active_task = c.fetchone()
    if active_task:
        conn.close()
        return jsonify({
            "error": "Active task in progress",
            "message": f"You already have active incident #{active_task['incident_id']} in progress. Finish your current task first!"
        }), 409

    # Atomic SQL Update
    c.execute('''
    UPDATE dispatches 
    SET status = 'Claimed', claimed_by = ?, claimed_at = CURRENT_TIMESTAMP
    WHERE id = ? AND status = 'Open'
    ''', (responder_id, dispatch_id))
    
    if c.rowcount == 0:
        # Check who claimed it
        c.execute('''
        SELECT d.status, r.name as responder_name 
        FROM dispatches d 
        LEFT JOIN responders r ON d.claimed_by = r.id 
        WHERE d.id = ?
        ''', (dispatch_id,))
        row = c.fetchone()
        conn.close()
        winner_name = row['responder_name'] if row and row['responder_name'] else "Another unit"
        return jsonify({
            "error": "Dispatch already claimed",
            "message": f"This emergency was already claimed by {winner_name}!"
        }), 409

    # Set responder status to 'Busy'
    c.execute("UPDATE responders SET status = 'Busy' WHERE id = ?", (responder_id,))

    # Update incident status to 'Assigned'
    c.execute("SELECT incident_id FROM dispatches WHERE id = ?", (dispatch_id,))
    inc_id = c.fetchone()['incident_id']
    c.execute("UPDATE incidents SET status = 'Assigned', updated_at = CURRENT_TIMESTAMP WHERE id = ? AND status = 'Reported'", (inc_id,))

    # Log audit
    c.execute("SELECT name FROM responders WHERE id = ?", (responder_id,))
    r_name = c.fetchone()['name']
    c.execute('''
    INSERT INTO audit_logs (incident_id, dispatch_id, actor, action, details)
    VALUES (?, ?, ?, 'CLAIM_ACCEPTED', ?)
    ''', (inc_id, dispatch_id, r_name, f"Accepted emergency claim. Unit status set to Busy."))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": f"Dispatch claimed successfully! Unit {r_name} assigned."
    })

@app.route('/api/responder/dispatch/<int:dispatch_id>/status', methods=['POST'])
def update_dispatch_status(dispatch_id):
    """
    Status progression: En Route -> Arrived -> Completed.
    Enforces valid sequence and frees driver on Completed.
    """
    data = request.get_json(silent=True) or {}
    new_status = (data.get('status') or "").strip()

    valid_transitions = {
        'Claimed': ['En Route'],
        'En Route': ['Arrived'],
        'Arrived': ['Completed']
    }

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM dispatches WHERE id = ?", (dispatch_id,))
    d = c.fetchone()
    if not d:
        conn.close()
        return jsonify({"error": "Dispatch not found"}), 404

    current_status = d['status']
    allowed_next = valid_transitions.get(current_status, [])

    if new_status not in allowed_next and new_status != current_status:
        conn.close()
        return jsonify({
            "error": "Invalid sequence",
            "message": f"Cannot transition from '{current_status}' to '{new_status}'. Allowed: {allowed_next}"
        }), 400

    c.execute("UPDATE dispatches SET status = ? WHERE id = ?", (new_status, dispatch_id))

    # Synchronize incident status
    inc_id = d['incident_id']
    if new_status in ('En Route', 'Arrived'):
        c.execute("UPDATE incidents SET status = 'In Progress', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (inc_id,))
    elif new_status == 'Completed':
        # Release responder to Available
        if d['claimed_by']:
            c.execute("UPDATE responders SET status = 'Available' WHERE id = ?", (d['claimed_by'],))
        
        # Check if all dispatches for this incident are completed
        c.execute("SELECT COUNT(*) FROM dispatches WHERE incident_id = ? AND status != 'Completed'", (inc_id,))
        remaining = c.fetchone()[0]
        if remaining == 0:
            c.execute("UPDATE incidents SET status = 'Resolved', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (inc_id,))

    # Audit log
    c.execute('''
    INSERT INTO audit_logs (incident_id, dispatch_id, actor, action, details)
    VALUES (?, ?, 'RESPONDER', 'DISPATCH_STATUS_PROGRESSION', ?)
    ''', (inc_id, dispatch_id, f"Responder transitioned dispatch to '{new_status}'"))

    conn.commit()
    conn.close()
    return jsonify({"success": True, "status": new_status, "message": f"Task status updated to {new_status}"})

@app.route('/api/responder/dispatch/<int:dispatch_id>/release', methods=['POST'])
def release_dispatch(dispatch_id):
    """
    Responder releases claim (e.g. breakdown, blocked route). Re-opens dispatch for others.
    """
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM dispatches WHERE id = ?", (dispatch_id,))
    d = c.fetchone()
    if not d:
        conn.close()
        return jsonify({"error": "Dispatch not found"}), 404

    old_responder = d['claimed_by']
    c.execute("UPDATE dispatches SET status = 'Open', claimed_by = NULL, claimed_at = NULL WHERE id = ?", (dispatch_id,))
    if old_responder:
        c.execute("UPDATE responders SET status = 'Available' WHERE id = ?", (old_responder,))

    c.execute('''
    INSERT INTO audit_logs (incident_id, dispatch_id, actor, action, details)
    VALUES (?, ?, 'RESPONDER', 'CLAIM_RELEASED', 'Responder released emergency claim back to open pool')
    ''', (d['incident_id'], dispatch_id))

    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Emergency claim released. Broadcasted back to available units."})

@app.route('/api/responder/location', methods=['POST'])
def update_responder_location():
    data = request.get_json() or {}
    resp_id = session.get('responder_id') or data.get('responder_id')
    lat = float(data.get('lat') or 0.0)
    lng = float(data.get('lng') or 0.0)

    if not resp_id or not lat or not lng:
        return jsonify({"error": "Missing coordinates or responder ID"}), 400

    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE responders SET lat = ?, lng = ?, last_seen = CURRENT_TIMESTAMP WHERE id = ?", (lat, lng, resp_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "lat": lat, "lng": lng})

# 6. Response Team CRUD & Auto-Assign Nearest Team (Module 1 & 3 Requirements)
@app.route('/api/responders', methods=['GET', 'POST'])
def manage_responders():
    conn = get_db()
    c = conn.cursor()

    if request.method == 'POST':
        data = request.get_json() or {}
        name = (data.get('name') or "").strip()
        unit_type = data.get('unit_type') or "Ambulance"
        station_name = (data.get('station_name') or "").strip()
        lat = float(data.get('lat') or 13.0827)
        lng = float(data.get('lng') or 80.2707)
        phone = (data.get('phone') or "").strip()
        status = data.get('status') or "Available"

        if not name or not station_name:
            conn.close()
            return jsonify({"error": "Name and station name are required"}), 400

        c.execute('''
        INSERT INTO responders (name, unit_type, station_name, lat, lng, phone, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, unit_type, station_name, lat, lng, phone, status))
        new_id = c.lastrowid
        conn.commit()
        conn.close()
        return jsonify({"success": True, "id": new_id, "message": f"Team {name} created"})

    # GET
    c.execute("SELECT * FROM responders ORDER BY id ASC")
    responders = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify({"responders": responders})

@app.route('/api/responders/<int:responder_id>/toggle-status', methods=['POST'])
def toggle_responder_status(responder_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT status FROM responders WHERE id = ?", (responder_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Responder not found"}), 404

    new_st = "Busy" if row['status'] == "Available" else "Available"
    c.execute("UPDATE responders SET status = ? WHERE id = ?", (new_st, responder_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "status": new_st})

@app.route('/api/incidents/<int:incident_id>/auto-assign', methods=['POST'])
def auto_assign_nearest_team(incident_id):
    """
    Requirement 3: Location-Based Nearest Team Assignment
    Calculates Haversine distance to find the nearest Available team matching the incident's category.
    One-click assigns the best-fit team, marks team Busy, and advances incident to Assigned.
    """
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
    inc = c.fetchone()
    if not inc:
        conn.close()
        return jsonify({"error": "Incident not found"}), 404

    # Determine needed unit type
    cat = inc['category'].lower()
    if 'fire' in cat:
        needed_type = 'Fire Engine'
    elif 'road' in cat or 'medical' in cat:
        needed_type = 'Ambulance'
    elif 'collapse' in cat or 'flood' in cat:
        needed_type = 'Fire Engine'
    else:
        needed_type = 'Police'

    # Find nearest available team
    c.execute("SELECT * FROM responders WHERE unit_type = ? AND status = 'Available'", (needed_type,))
    available_teams = c.fetchall()

    if not available_teams:
        # Fallback to any available responder if preferred is out of stock
        c.execute("SELECT * FROM responders WHERE status = 'Available'")
        available_teams = c.fetchall()

    if not available_teams:
        conn.close()
        return jsonify({"error": f"No available {needed_type} or backup emergency units currently online"}), 400

    best_team = None
    min_dist = float('inf')
    for t in available_teams:
        d = haversine_km(inc['lat'], inc['lng'], t['lat'], t['lng'])
        if d < min_dist:
            min_dist = d
            best_team = t

    # Create or update dispatch to Claimed
    c.execute('''
    SELECT id FROM dispatches 
    WHERE incident_id = ? AND unit_type = ? AND status = 'Open'
    LIMIT 1
    ''', (incident_id, best_team['unit_type']))
    disp = c.fetchone()

    if disp:
        dispatch_id = disp['id']
        c.execute('''
        UPDATE dispatches 
        SET status = 'Claimed', claimed_by = ?, claimed_at = CURRENT_TIMESTAMP 
        WHERE id = ?
        ''', (best_team['id'], dispatch_id))
    else:
        c.execute('''
        INSERT INTO dispatches (incident_id, unit_type, status, claimed_by, claimed_at)
        VALUES (?, ?, 'Claimed', ?, CURRENT_TIMESTAMP)
        ''', (incident_id, best_team['unit_type'], best_team['id']))
        dispatch_id = c.lastrowid

    # Mark team Busy and incident Assigned
    c.execute("UPDATE responders SET status = 'Busy' WHERE id = ?", (best_team['id'],))
    c.execute("UPDATE incidents SET status = 'Assigned', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (incident_id,))

    # Audit log
    c.execute('''
    INSERT INTO audit_logs (incident_id, dispatch_id, actor, action, details)
    VALUES (?, ?, 'ADMIN_AUTO_ASSIGN', ?)
    ''', (incident_id, dispatch_id, f"Auto-assigned nearest unit '{best_team['name']}' ({min_dist}km away)"))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": f"Successfully auto-assigned {best_team['name']} ({min_dist} km away)",
        "team": dict(best_team),
        "distance_km": min_dist
    })

# 7. Operational Analytics KPIs (Module 6 Requirement)
@app.route('/api/stats', methods=['GET'])
def get_operational_stats():
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM incidents")
    total_incidents = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM incidents WHERE final_severity = 'Critical'")
    critical_incidents = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM incidents WHERE status = 'Assigned'")
    assigned_incidents = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM incidents WHERE status = 'Resolved'")
    resolved_incidents = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM responders WHERE status = 'Available'")
    available_teams = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM responders WHERE status = 'Busy'")
    busy_teams = c.fetchone()[0]

    # Category distribution
    c.execute("SELECT category, COUNT(*) as cnt FROM incidents GROUP BY category")
    cat_counts = {row['category']: row['cnt'] for row in c.fetchall()}

    # Severity distribution
    c.execute("SELECT final_severity, COUNT(*) as cnt FROM incidents GROUP BY final_severity")
    sev_counts = {row['final_severity']: row['cnt'] for row in c.fetchall()}

    conn.close()
    return jsonify({
        "total_incidents": total_incidents,
        "critical_incidents": critical_incidents,
        "assigned_incidents": assigned_incidents,
        "resolved_incidents": resolved_incidents,
        "available_teams": available_teams,
        "busy_teams": busy_teams,
        "category_distribution": cat_counts,
        "severity_distribution": sev_counts
    })

# 8. Photo serving
@app.route('/api/reports/<int:incident_id>/photo', methods=['GET'])
def get_incident_photo(incident_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT photo_filename FROM incidents WHERE id = ?", (incident_id,))
    row = c.fetchone()
    conn.close()

    if not row or not row['photo_filename']:
        return jsonify({"error": "No photo available"}), 404

    return send_from_directory(app.config['UPLOAD_FOLDER'], row['photo_filename'])

# -------------------------------------------------------------
# Frontend Page Routes (Templates)
# -------------------------------------------------------------
@app.route('/')
def index_page():
    # Citizen reporting form by default
    return render_template("citizen.html")

@app.route('/track/<int:incident_id>')
def track_page(incident_id):
    return render_template("track.html", incident_id=incident_id)

@app.route('/admin')
def admin_page():
    return render_template("admin.html")

@app.route('/responder')
def responder_page():
    return render_template("responder.html")

# -------------------------------------------------------------
# App Runner
# -------------------------------------------------------------
if __name__ == '__main__':
    init_db()
    seed_demo_data()
    print("\n=======================================================")
    print("CrisisGuard Intelligent Emergency Platform (Round 2)")
    print("Serving on http://localhost:5000")
    print("=======================================================\n")
    app.run(host='0.0.0.0', port=5000, debug=True)
