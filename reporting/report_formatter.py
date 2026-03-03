import os
import json
from datetime import datetime
from typing import Dict


class ReportFormatter:
    """
    Handles formatting and saving of incident reports.
    """

    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        print(f"✅ Report Formatter ready — saving to /{output_dir}/")

    def print_report(self, report_text: str, rca_data: Dict):
        """Prints report to terminal with formatting"""
        sev     = rca_data.get("severity", "?")
        service = rca_data.get("root_cause_service", "unknown")
        inc_id  = rca_data.get("incident_id", "unknown")

        print("\n")
        print("🚨" * 30)
        print(f"  INCIDENT REPORT — SEV-{sev} | {service} | {inc_id}")
        print("🚨" * 30)
        print(report_text)
        print("=" * 65)

    def save_report(self, report_text: str, rca_data: Dict) -> str:
        """
        Saves report to a .txt file in /reports/ directory.
        Returns the saved file path.
        """
        inc_id  = rca_data.get("incident_id", "unknown")
        service = rca_data.get(
            "root_cause_service", "unknown"
        ).replace("-", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save text report
        txt_file = f"{self.output_dir}/{inc_id}_{service}.txt"
        with open(txt_file, "w", encoding="utf-8") as f:
            f.write(f"Incident ID : {inc_id}\n")
            f.write(f"Generated   : {timestamp}\n")
            f.write(f"Service     : {service}\n")
            f.write("=" * 65 + "\n\n")
            f.write(report_text)

        # Save raw RCA data as JSON
        json_file = f"{self.output_dir}/{inc_id}_raw.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(rca_data, f, indent=2, default=str)

        print(f"💾 Report saved  → {txt_file}")
        print(f"💾 Raw data saved → {json_file}")

        return txt_file