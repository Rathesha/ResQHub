import os
import sys
from app import app, init_db, seed_demo_data

if __name__ == '__main__':
    init_db()
    seed_demo_data()
    cert_path = os.path.join(os.path.dirname(__file__), 'cert.pem')
    key_path = os.path.join(os.path.dirname(__file__), 'key.pem')

    print("\n=======================================================")
    print("CrisisGuard HTTPS Phone Server (Live Camera & GPS Ready)")
    print("LAN URL: https://192.168.137.190:5000")
    print("Local URL: https://localhost:5000")
    print("=======================================================\n")

    app.run(host='0.0.0.0', port=5000, ssl_context=(cert_path, key_path), debug=False)
