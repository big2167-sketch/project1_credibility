from __future__ import annotations

from typing import Any, Dict, List


SYSTEM_INSTRUCTIONS = """
You are simulating a realistic user persona testing an app feature.
You must give feedback that matches the persona traits and constraints.
Be specific: mention what you like, what is confusing, and what you would change.

Follow this exact output structure:

1) Overall reaction (2-4 sentences)
2) What works well (bullets, 2-5)
3) Concerns / pain points (bullets, 2-6)
4) Suggestions / improvements (bullets, 2-6)
5) Likelihood to use (0-10) + 1 sentence why
6) Follow-up questions the persona would ask (bullets, 1-4)

Do not add extra sections.
""".strip()


def _persona_block(persona: Dict[str, Any]) -> str:
    """
    Builds a consistent persona block, supporting either:
    - your 'personas.json' style (name/demographics/goals/etc), OR
    - a simpler style (name/description/traits).
    """
    name = persona.get("name", "Unknown Persona")
    description = persona.get("description", "")
    traits = persona.get("traits", {})

    demographics = persona.get("demographics", "")
    goals = persona.get("goals", [])
    frustrations = persona.get("frustrations", [])
    tech_level = persona.get("tech_level", "")
    accessibility = persona.get("accessibility_needs", [])
    tone = persona.get("tone", "")

    lines = [f"Name: {name}"]

    if demographics:
        lines.append(f"Demographics: {demographics}")
    if goals:
        lines.append(f"Goals: {', '.join(goals)}")
    if frustrations:
        lines.append(f"Frustrations: {', '.join(frustrations)}")
    if tech_level:
        lines.append(f"Tech level: {tech_level}")
    if accessibility:
        lines.append(f"Accessibility needs: {', '.join(accessibility)}")
    if tone:
        lines.append(f"Tone: {tone}")

    if description:
        lines.append(f"Description: {description}")
    if traits:
        lines.append(f"Traits: {traits}")

    return "\n".join(lines).strip()


# ----------------------------
# Prompt builders used by simulator.py
# ----------------------------
def build_user_prompt(feature_description: str, persona: Dict[str, Any]) -> str:
    persona_block = _persona_block(persona)

    return f"""
You are the persona below. Evaluate the feature exactly as that persona would.

PERSONA
{persona_block}

FEATURE TO EVALUATE
{feature_description}

Remember: follow the exact output structure in the system instructions.
""".strip()


def build_followup_prompt(
    feature_description: str,
    persona: Dict[str, Any],
    chat_history: List[Dict[str, str]],
    user_question: str,
) -> str:
    persona_block = _persona_block(persona)

    convo_text = ""
    for msg in chat_history:
        role = (msg.get("role") or "").upper()
        content = msg.get("content") or ""
        convo_text += f"{role}: {content}\n"

    return f"""
You are continuing a simulated conversation as the persona below.

PERSONA
{persona_block}

FEATURE BEING DISCUSSED
{feature_description}

CONVERSATION SO FAR
{convo_text.strip()}

USER FOLLOW-UP QUESTION
{user_question}

Respond as the persona. Be specific, realistic, and consistent with the persona constraints.
Do not break character.
""".strip()


def build_analysis_prompt(feature_description: str, persona_outputs: List[Dict[str, Any]]) -> str:
    """
    persona_outputs expected list items:
      {
        "persona_name": str,
        "persona": dict,
        "feedback": str
      }
    """
    compiled = ""
    for item in persona_outputs:
        pname = item.get("persona_name", "Unknown")
        fb = item.get("feedback", "")
        compiled += f"\n---\nPersona: {pname}\nFeedback:\n{fb}\n"

    return f"""
You are analyzing simulated feedback from multiple personas about a feature.

FEATURE
{feature_description}

PERSONA FEEDBACK
{compiled.strip()}

Produce:

A) Common themes (bullets)
B) Major disagreements (bullets)
C) Top 5 prioritized fixes (numbered list, most important first)
D) Risks if not fixed (bullets)
E) Short product recommendation summary (4-6 sentences)

Keep it concise and actionable.
""".strip()
