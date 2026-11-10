from app import get_db

conn = get_db()
c = conn.cursor()
c.execute("UPDATE responders SET status = 'Available'")
c.execute("DELETE FROM users WHERE username LIKE 'resp%'")
c.execute("DELETE FROM responders WHERE id NOT IN (1, 2, 3, 5, 6)")
conn.commit()

c.execute("SELECT id, name, unit_type, status, phone FROM responders ORDER BY id ASC")
print("Remaining Responders:")
for r in c.fetchall():
    print(f"[{r[0]}] {r[1]} - {r[2]} ({r[3]}) - {r[4]}")

c.execute("SELECT id, username, role, responder_id FROM users")
print("\nUsers:")
for u in c.fetchall():
    print(f"[{u[0]}] {u[1]} ({u[2]}) -> resp {u[3]}")

conn.close()
