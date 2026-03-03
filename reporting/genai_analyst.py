import os
import sys
from typing import Dict
from dotenv import load_dotenv

load_dotenv()

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


class GenAIAnalyst:
    """
    Uses Groq's free Llama 3 API to generate professional
    incident reports from structured RCA data.
    """

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key or api_key == "gsk_xxxxxxxxxxxxxxxxxxxx":
            print("⚠️  WARNING: GROQ_API_KEY not set in .env")
            print("   Using fallback template report instead")
            self.client = None
        else:
            try:
                from groq import Groq
                self.client = Groq(api_key=api_key)
                print("✅ GenAI Analyst connected to Groq (Llama 3 — FREE)!")
            except ImportError:
                print("❌ groq library not installed!")
                print("   Run: pip install groq")
                self.client = None

    def generate_report(self, rca_report: Dict) -> str:
        """
        Generates a full incident report using Groq API.
        Falls back to template if API unavailable.
        """

        if not self.client:
            return self._fallback_report(rca_report)

        prompt = self._build_prompt(rca_report)

        print("🤖 Sending RCA data to Groq (Llama 3)...")

        try:
            response = self.client.chat.completions.create(
                # Best free model on Groq — very capable
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        # System prompt tells the model its role
                        "role": "system",
                        "content": (
                            "You are an expert Site Reliability Engineer "
                            "writing professional incident reports. "
                            "Be concise, technical, and actionable. "
                            "Engineers are reading this under pressure."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                # Max tokens for the response
                max_tokens=1500,
                # Temperature 0.3 = focused and consistent output
                # Lower = more deterministic, less creative
                temperature=0.3,
            )

            report_text = response.choices[0].message.content
            print("✅ Groq API response received!")
            return report_text

        except Exception as e:
            print(f"❌ Groq API error: {e}")
            print("   Falling back to template report...")
            return self._fallback_report(rca_report)

    def _build_prompt(self, rca: Dict) -> str:
        """Builds detailed prompt with all RCA data"""

        blast   = rca.get("blast_radius", {})
        primary = rca.get("primary_anomaly", {})

        prompt = f"""Generate a professional SRE incident report from this automated analysis:

=== INCIDENT DATA ===
Incident ID     : {rca.get('incident_id')}
Timestamp       : {rca.get('timestamp')}
Severity        : SEV-{rca.get('severity')}
Affected Service: {rca.get('root_cause_service')}
Owning Team     : {rca.get('owning_team')}

=== ANOMALY DETAILS ===
Type            : {primary.get('type', '').replace('_', ' ')}
Observed Value  : {primary.get('observed_value')}
Expected Value  : {primary.get('expected_value')}
Anomaly Severity: {primary.get('severity')}/4

=== BLAST RADIUS ===
Directly Affected  : {blast.get('directly_affected', [])}
Indirectly Affected: {blast.get('indirectly_affected', [])}
Total Services Hit : {blast.get('total_affected', 0)}

=== ROOT CAUSE ===
{rca.get('root_cause_summary')}

=== TOP HYPOTHESES ===
{chr(10).join(f"- {h}" for h in rca.get('hypotheses', []))}

=== RECOMMENDED FIXES ===
{chr(10).join(f"- {f}" for f in rca.get('recommended_fixes', []))}

=== SIMILAR PAST INCIDENTS ===
{rca.get('similar_incidents', 'None')}

Write the report with these exact sections:

1. INCIDENT SUMMARY
2. BUSINESS IMPACT  
3. TIMELINE
4. ROOT CAUSE
5. AFFECTED SERVICES
6. IMMEDIATE ACTIONS (numbered steps)
7. LONG-TERM RECOMMENDATIONS
8. LESSONS LEARNED

Be concise and actionable. No fluff."""

        return prompt

    def _fallback_report(self, rca: Dict) -> str:
        """Template report when API is unavailable"""

        blast   = rca.get("blast_radius", {})
        primary = rca.get("primary_anomaly", {})
        service = rca.get("root_cause_service", "unknown")
        sev     = rca.get("severity", "?")
        fixes   = rca.get("recommended_fixes", [])
        hyps    = rca.get("hypotheses", [])

        return f"""
{'='*65}
INCIDENT REPORT — SEV-{sev}    [{rca.get('incident_id')}]
{'='*65}
Time    : {rca.get('timestamp')}
Service : {service}
Team    : {rca.get('owning_team', 'unknown')}
{'='*65}

1. INCIDENT SUMMARY
   {service} is experiencing {primary.get('type','').replace('_',' ')}.
   Observed: {primary.get('observed_value')} | Expected: {primary.get('expected_value')}
   {blast.get('total_affected', 0)} downstream services affected.

2. BUSINESS IMPACT
   Directly affected  : {blast.get('directly_affected', [])}
   Indirectly affected: {blast.get('indirectly_affected', [])}
   User impact: HIGH — checkout and order flows degraded.

3. ROOT CAUSE
   {rca.get('root_cause_summary')}

4. TOP HYPOTHESES
{chr(10).join(f'   {i+1}. {h}' for i, h in enumerate(hyps[:3]))}

5. IMMEDIATE ACTIONS
{chr(10).join(f'   {i+1}. {f}' for i, f in enumerate(fixes[:4]))}

6. LONG-TERM RECOMMENDATIONS
   - Add auto-scaling policies for {service}
   - Implement circuit breakers on all downstream calls
   - Set proactive alerts before thresholds are breached
   - Schedule post-incident review within 48 hours

7. SIMILAR PAST INCIDENTS
   Reference: {rca.get('similar_incidents', [])}

8. LESSONS LEARNED
   - Automated detection caught this in under 60 seconds
   - Cascade failures need circuit breakers to stop propagation

{'='*65}
Generated by Project 71 AIOps Platform — Powered by Groq
{'='*65}
"""