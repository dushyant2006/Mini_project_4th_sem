# ============================================================
# reporting/report_engine.py
# PURPOSE: Listens to rca.results, generates AI reports
#          using Groq + saves all 3 template formats
# ============================================================

import json
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from kafka import KafkaConsumer
from reporting.genai_analyst    import GenAIAnalyst
from reporting.report_formatter import ReportFormatter
from reporting.report_templates import generate_report

TOPIC_RCA = "rca.results"


def run_report_engine():
    print("=" * 60)
    print("  PROJECT 71 — GENAI REPORT ENGINE")
    print("=" * 60)
    print(f"  Input    : {TOPIC_RCA}")
    print(f"  Model    : Groq Llama 3 (FREE)")
    print(f"  Output   : /reports/ directory")
    print(f"  Templates: standard | executive | technical")
    print("=" * 60)

    analyst   = GenAIAnalyst()
    formatter = ReportFormatter(output_dir="reports")

    consumer = KafkaConsumer(
        TOPIC_RCA,
        bootstrap_servers="localhost:9092",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="latest",
        group_id="report-engine",
        enable_auto_commit=True,
        api_version=(2, 0, 0),
    )

    print("\n✅ Report Engine running... Press Ctrl+C to stop")
    print("   Waiting for RCA results...\n")
    print("-" * 60)

    reports_generated = 0

    try:
        while True:
            records = consumer.poll(timeout_ms=1000)
            if not records:
                continue

            for tp, messages in records.items():
                for msg in messages:
                    rca_data = msg.value

                    print(f"\n📨 Received RCA result:")
                    print(f"   Incident : {rca_data.get('incident_id')}")
                    print(f"   Service  : {rca_data.get('root_cause_service')}")
                    print(f"   Severity : SEV-{rca_data.get('severity')}")
                    print(f"\n🤖 Generating AI report + 3 templates...")

                    # ── Groq AI Report ────────────────────────
                    report_text = analyst.generate_report(rca_data)
                    formatter.print_report(report_text, rca_data)
                    filepath = formatter.save_report(report_text, rca_data)

                    # ── Save All 3 Templates ──────────────────
                    inc_id = rca_data.get("incident_id", "UNKNOWN")
                    svc    = rca_data.get(
                        "root_cause_service", "unknown"
                    ).replace("-", "_")

                    os.makedirs("reports", exist_ok=True)

                    for template_name in ["standard", "executive", "technical"]:
                        try:
                            content = generate_report(
                                rca_data, template=template_name
                            )
                            path = os.path.join(
                                "reports",
                                f"{inc_id}_{svc}_{template_name}.txt"
                            )
                            with open(path, "w", encoding="utf-8") as f:
                                f.write(content)
                            print(f"   📄 {template_name.capitalize()} template → {path}")
                        except Exception as e:
                            print(f"   ⚠️ Template '{template_name}' error: {e}")

                    reports_generated += 1
                    print(f"\n✅ Report #{reports_generated} complete!")
                    print(f"   AI report  : {filepath}")
                    print(f"   Templates  : standard + executive + technical")

    except KeyboardInterrupt:
        print(f"\n⛔ Report Engine stopped.")
        print(f"   Total reports generated: {reports_generated}")
        print(f"   Check /reports/ folder for saved files")
    finally:
        consumer.close()


if __name__ == "__main__":
    run_report_engine()