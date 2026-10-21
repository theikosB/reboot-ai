
import os

from dotenv import load_dotenv
from google import genai

load_dotenv()


def create_restart_plan(report: dict) -> str:
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Add it to your .env file."
        )

    client = genai.Client(api_key=api_key)

    project_context = f"""
Project path: {report['path']}

README:
{report['readme'][:3000]}

Recent commits:
{chr(10).join(report['commits'])}

Tracked files:
{chr(10).join(report['files'][:50])}

TODO markers:
{chr(10).join(report['todos'])}
"""

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=f"""
You are Reboot, a practical project-revival assistant.

Use only the supplied evidence. Do not invent project history
or claim that you inspected files not supplied.

Explain what the project appears to do, identify likely
unfinished work, and recommend exactly three concrete next
steps. Clearly label uncertain inferences.

Create a concise restart brief for this project:

{project_context}
""",
    )

    return response.text or "The model returned an empty response."
