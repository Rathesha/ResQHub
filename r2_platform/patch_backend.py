import re

with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Update seed_demo_data
pattern_seed = r'def seed_demo_data\(\):.*?(?=\n# ---|\n# -------------------------------------------------------------)'
new_seed = '''def seed_demo_data():
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
            c.execute(\'\'\'
            UPDATE responders SET name = ?, unit_type = ?, station_name = ?, lat = ?, lng = ? WHERE id = ?
            \'\'\', (full_display_name, u_type, station, lat, lng, resp_id))
        else:
            c.execute(\'\'\'
            INSERT INTO responders (name, unit_type, station_name, lat, lng, phone, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            \'\'\', (full_display_name, u_type, station, lat, lng, phone, st))
            resp_id = c.lastrowid

        # Upsert user account (password: responder123)
        pwd_hash = generate_password_hash("responder123")
        c.execute("SELECT id FROM users WHERE username = ?", (uname,))
        user_row = c.fetchone()
        if user_row:
            c.execute("UPDATE users SET password_hash = ?, responder_id = ? WHERE id = ?", (pwd_hash, resp_id, user_row[0]))
        else:
            c.execute(\'\'\'
            INSERT INTO users (username, password_hash, role, responder_id)
            VALUES (?, ?, 'responder', ?)
            \'\'\', (uname, pwd_hash, resp_id))

    # Admin user (admin / admin123)
    admin_pwd = generate_password_hash("admin123")
    c.execute("SELECT id FROM users WHERE username = 'admin'")
    admin_row = c.fetchone()
    if admin_row:
        c.execute("UPDATE users SET password_hash = ? WHERE id = ?", (admin_pwd, admin_row[0]))
    else:
        c.execute(\'\'\'
        INSERT INTO users (username, password_hash, role, responder_id)
        VALUES ('admin', ?, 'admin', NULL)
        \'\'\', (admin_pwd,))

    conn.commit()
    conn.close()
    print("Idempotently seeded 5 demo responder accounts (amb01..03, fe01..02 / responder123) and admin.")'''

code = re.sub(pattern_seed, new_seed, code, flags=re.DOTALL)

# 2. Update trigger_dispatches_for_incident to return total_alerts_sent
pattern_trigger = r'def trigger_dispatches_for_incident\(incident_id: int, db_conn, radius_km: float = 8\.0\):.*?(?=\n# ---|\n# -------------------------------------------------------------)'
new_trigger = '''def trigger_dispatches_for_incident(incident_id: int, db_conn, radius_km: float = 25.0):
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
        c.execute(\'\'\'
        SELECT id, status FROM dispatches 
        WHERE incident_id = ? AND unit_type = ? AND status IN ('Open', 'Claimed', 'En Route', 'Arrived')
        \'\'\', (incident_id, unit_type))
        existing_dispatch = c.fetchone()
        
        if existing_dispatch:
            dispatch_id = existing_dispatch['id']
        else:
            c.execute(\'\'\'
            INSERT INTO dispatches (incident_id, unit_type, status)
            VALUES (?, ?, 'Open')
            \'\'\', (incident_id, unit_type))
            dispatch_id = c.lastrowid

            # Log audit
            c.execute(\'\'\'
            INSERT INTO audit_logs (incident_id, dispatch_id, actor, action, details)
            VALUES (?, ?, 'SYSTEM', 'DISPATCH_BROADCAST_CREATED', ?)
            \'\'\', (incident_id, dispatch_id, f"Broadcast open for {unit_type} units within {radius_km}km"))

        # Broadcast to all matching Available responders within radius
        c.execute(\'\'\'
        SELECT id, lat, lng FROM responders 
        WHERE unit_type = ? AND status = 'Available'
        \'\'\', (unit_type,))
        for resp in c.fetchall():
            dist = haversine_km(inc['lat'], inc['lng'], resp['lat'], resp['lng'])
            if dist <= radius_km:
                c.execute(\'\'\'
                INSERT OR IGNORE INTO dispatch_alerts (dispatch_id, responder_id, distance_km)
                VALUES (?, ?, ?)
                \'\'\', (dispatch_id, resp['id'], dist))
                total_alerts_sent += 1

    db_conn.commit()
    return total_alerts_sent'''

code = re.sub(pattern_trigger, new_trigger, code, flags=re.DOTALL)

# 3. Update submit_report to handle optional photo and return alerts_sent
old_submit_start = '''    # Validate Photo (Mandatory Live Camera Capture)
    photo_filename = None
    photo_hash = None
    if not photo_b64:
        return jsonify({"error": "Mandatory live camera evidence photo is missing"}), 400'''

new_submit_start = '''    # Validate Photo (Optional in Step 4)
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
            print("Warning: Photo decode skipped:", e)'''

# Also update the photo decode try block replacement in submit_report
pattern_submit = r'    # Validate Photo \(Mandatory Live Camera Capture\).*?with open\(photo_path, "wb"\) as f:\s*f\.write\(photo_bytes\)\s*except Exception as e:\s*return jsonify\(\{"error": f"Failed to decode photo: \{str\(e\)\}"\}\), 400'
code = re.sub(pattern_submit, new_submit_start, code, flags=re.DOTALL)

# Update trigger_dispatches call in submit_report and response
old_sub_trigger = '''    # Trigger Zomato/Swiggy-style Dispatch Alerts immediately if not held for verification
    if initial_status != "Needs Verification":
        trigger_dispatches_for_incident(incident_id, conn)

    conn.close()

    return jsonify({
        "success": True,
        "incident_id": incident_id,
        "language": lang,
        "rule_severity": rule_sev,
        "ai_severity": ai_sev,
        "final_severity": final_sev,
        "trust_score": trust_score,
        "trust_label": trust_label,
        "status": initial_status,
        "message": "Emergency incident registered and dispatched successfully"
    }), 201'''

new_sub_trigger = '''    # Trigger Zomato/Swiggy-style Dispatch Alerts immediately if not held for verification
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
    }), 201'''

code = code.replace(old_sub_trigger, new_sub_trigger)

# 4. Update track_incident to include alerts_count
old_track = '''    return jsonify({
        "incident": dict(inc),
        "dispatches": dispatches
    })'''

new_track = '''    # Compute total alerts sent across all dispatches for this incident
    c = get_db().cursor()
    c.execute(\'\'\'
    SELECT COUNT(DISTINCT responder_id) FROM dispatch_alerts 
    WHERE dispatch_id IN (SELECT id FROM dispatches WHERE incident_id = ?)
    \'\'\', (incident_id,))
    alerts_sent_count = c.fetchone()[0]

    return jsonify({
        "incident": dict(inc),
        "dispatches": dispatches,
        "alerts_sent": alerts_sent_count,
        "tracking_code": f"RQ-{incident_id:04d}"
    })'''

code = code.replace(old_track, new_track)

# 5. Enforce One Active Task per Driver & atomic accept in accept_dispatch
old_accept = '''@app.route('/api/responder/dispatch/<int:dispatch_id>/accept', methods=['POST'])
def accept_dispatch(dispatch_id):
    """
    ATOMIC FIRST-ACCEPT-WINS MECHANIC (Zomato/Swiggy model):
    UPDATE dispatches SET status='Claimed', claimed_by=?, claimed_at=CURRENT_TIMESTAMP 
    WHERE id=? AND status='Open'
    Only the first request succeeds; any subsequent request receives 409 Conflict.
    """
    responder_id = session.get('responder_id') or request.json.get('responder_id', 1)

    conn = get_db()
    c = conn.cursor()

    # Atomic SQL Update
    c.execute(\'\'\'
    UPDATE dispatches 
    SET status = 'Claimed', claimed_by = ?, claimed_at = CURRENT_TIMESTAMP
    WHERE id = ? AND status = 'Open'
    \'\'\', (responder_id, dispatch_id))
    
    if c.rowcount == 0:
        # Check who claimed it
        c.execute(\'\'\'
        SELECT d.status, r.name as responder_name 
        FROM dispatches d 
        LEFT JOIN responders r ON d.claimed_by = r.id 
        WHERE d.id = ?
        \'\'\', (dispatch_id,))
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
    c.execute(\'\'\'
    INSERT INTO audit_logs (incident_id, dispatch_id, actor, action, details)
    VALUES (?, ?, ?, 'CLAIM_ACCEPTED', ?)
    \'\'\', (inc_id, dispatch_id, r_name, f"Accepted emergency claim. Unit status set to Busy."))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": f"Dispatch claimed successfully! Unit {r_name} assigned."
    })'''

new_accept = '''@app.route('/api/responder/dispatch/<int:dispatch_id>/accept', methods=['POST'])
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
    c.execute(\'\'\'
    SELECT id, incident_id, status FROM dispatches 
    WHERE claimed_by = ? AND status IN ('Claimed', 'En Route', 'Arrived')
    LIMIT 1
    \'\'\', (responder_id,))
    active_task = c.fetchone()
    if active_task:
        conn.close()
        return jsonify({
            "error": "Active task in progress",
            "message": f"You already have active incident #{active_task['incident_id']} in progress. Finish your current task first!"
        }), 409

    # Atomic SQL Update
    c.execute(\'\'\'
    UPDATE dispatches 
    SET status = 'Claimed', claimed_by = ?, claimed_at = CURRENT_TIMESTAMP
    WHERE id = ? AND status = 'Open'
    \'\'\', (responder_id, dispatch_id))
    
    if c.rowcount == 0:
        # Check who claimed it
        c.execute(\'\'\'
        SELECT d.status, r.name as responder_name 
        FROM dispatches d 
        LEFT JOIN responders r ON d.claimed_by = r.id 
        WHERE d.id = ?
        \'\'\', (dispatch_id,))
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
    c.execute(\'\'\'
    INSERT INTO audit_logs (incident_id, dispatch_id, actor, action, details)
    VALUES (?, ?, ?, 'CLAIM_ACCEPTED', ?)
    \'\'\', (inc_id, dispatch_id, r_name, f"Accepted emergency claim. Unit status set to Busy."))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": f"Dispatch claimed successfully! Unit {r_name} assigned."
    })'''

code = code.replace(old_accept, new_accept)

# 6. Update update_dispatch_status to enforce valid sequence: En Route -> Arrived -> Completed
old_status_func = '''@app.route('/api/responder/dispatch/<int:dispatch_id>/status', methods=['POST'])
def update_dispatch_status(dispatch_id):
    """
    Status progression: Claimed -> En Route -> Arrived -> Completed
    """
    data = request.get_json() or {}
    new_status = data.get('status') # 'En Route', 'Arrived', 'Completed'

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM dispatches WHERE id = ?", (dispatch_id,))
    d = c.fetchone()
    if not d:
        conn.close()
        return jsonify({"error": "Dispatch not found"}), 404

    c.execute("UPDATE dispatches SET status = ? WHERE id = ?", (new_status, dispatch_id))

    # Synchronize incident status
    inc_id = d['incident_id']
    if new_status in ('En Route', 'Arrived'):
        c.execute("UPDATE incidents SET status = 'In Progress', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (inc_id,))
    elif new_status == 'Completed':
        # Release responder
        if d['claimed_by']:
            c.execute("UPDATE responders SET status = 'Available' WHERE id = ?", (d['claimed_by'],))
        
        # Check if all dispatches for this incident are completed
        c.execute("SELECT COUNT(*) FROM dispatches WHERE incident_id = ? AND status != 'Completed'", (inc_id,))
        remaining = c.fetchone()[0]
        if remaining == 0:
            c.execute("UPDATE incidents SET status = 'Resolved', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (inc_id,))

    # Audit log
    c.execute(\'\'\'
    INSERT INTO audit_logs (incident_id, dispatch_id, actor, action, details)
    VALUES (?, ?, 'RESPONDER', 'DISPATCH_STATUS_PROGRESSION', ?)
    \'\'\', (inc_id, dispatch_id, f"Responder transitioned dispatch to '{new_status}'"))

    conn.commit()
    conn.close()
    return jsonify({"success": True, "status": new_status})'''

new_status_func = '''@app.route('/api/responder/dispatch/<int:dispatch_id>/status', methods=['POST'])
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
    c.execute(\'\'\'
    INSERT INTO audit_logs (incident_id, dispatch_id, actor, action, details)
    VALUES (?, ?, 'RESPONDER', 'DISPATCH_STATUS_PROGRESSION', ?)
    \'\'\', (inc_id, dispatch_id, f"Responder transitioned dispatch to '{new_status}'"))

    conn.commit()
    conn.close()
    return jsonify({"success": True, "status": new_status, "message": f"Task status updated to {new_status}"})'''

code = code.replace(old_status_func, new_status_func)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Updated app.py with all backend fixes!")
