"""
NetSage AI — Main Application Launcher
Runs database migration/seeding and starts the HTTP application server.
"""

import os
import sys
import webbrowser

# Add current directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.db import init_db, get_all_cases
from backend.seed_data import seed
from backend.server import run_server, PORT

def main():
    print("=" * 65)
    print("   NetSage AI -- Applied AI + Network Troubleshooting")
    print("   Cisco Applied AI + Network Troubleshooting Internship Project")
    print("=" * 65)

    # Initialize DB & Seed if empty
    init_db()
    cases = get_all_cases()
    if len(cases) < 30:
        print(f"[*] Ingesting dataset (current cases: {len(cases)})...")
        seed()
    else:
        print(f"[OK] Database loaded with {len(cases)} troubleshooting cases.")

    print(f"\n[+] NetSage AI Web Interface available at: http://localhost:{PORT}")
    print("[+] Press Ctrl+C to stop the server.\n")

    run_server(PORT)

if __name__ == "__main__":
    main()
