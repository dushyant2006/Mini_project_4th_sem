import json
import sys
import os
from kafka import KafkaConsumer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from reporting.genai_analyst    import GenAIAnalyst
from reporting.report_formatter import ReportFormatter

TOPIC_RCA = "rca.results"


def run_report_engine():
    print("=" * 60)
    print("  PROJECT 71 — GENAI REPORT ENGINE")
    print("=" * 60)
    print(f"  Input : {TOPIC_RCA}")
    print(f"  Model : Groq Llama 3 (FREE)")
    print(f"  Output: /reports/ directory")
    print("=" * 60)

    # Initialize components
    analyst   = GenAIAnalyst()
    formatter = ReportFormatter(output_dir="reports")

    # Kafka consumer
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
                    print(f"\n🤖 Generating AI report...")

                    # Generate report using Groq API
                    report_text = analyst.generate_report(rca_data)

                    # Print to terminal
                    formatter.print_report(report_text, rca_data)

                    # Save to file
                    filepath = formatter.save_report(
                        report_text, rca_data
                    )

                    reports_generated += 1
                    print(f"\n✅ Report #{reports_generated} complete!")
                    print(f"   Saved to: {filepath}")

    except KeyboardInterrupt:
        print(f"\n⛔ Report Engine stopped.")
        print(f"   Total reports generated: {reports_generated}")
        print(f"   Check /reports/ folder for saved files")
    finally:
        consumer.close()


if __name__ == "__main__":
    run_report_engine()