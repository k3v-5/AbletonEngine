from server import AbletonConnection
from engine.production.doctor.session_doctor import CopilotSessionDoctor
import json

def main():
    conn = AbletonConnection("localhost", 9877)
    if not conn.connect():
        print("Failed to connect")
        return

    doc = CopilotSessionDoctor()
    issues, summary, raw_tracks = doc._scan_session(conn)
    
    with open("scripts/doctor_issues_report.json", "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "issues": issues}, f, indent=2, ensure_ascii=False)
    
    print("SAVED REPORT. Total issues:", len(issues))
    for iss in issues:
        print(f"[{iss['id']}] ({iss['category']} - {iss['severity']}) Track {iss.get('track_index')}: {iss['track_name']} -> Action: {iss.get('recommended_params', {}).get('action')}")

    conn.disconnect()

if __name__ == "__main__":
    main()
