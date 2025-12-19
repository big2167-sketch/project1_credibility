from __future__ import annotations

from typing import Any, Dict, List, Optional

from openai import OpenAI

from .utility import load_env, get_api_key
from .prompts import (
    SYSTEM_INSTRUCTIONS,
    build_user_prompt,
    build_analysis_prompt,
    build_followup_prompt,
)

def analyze_feedback(feedback: str) -> dict:
    # TODO: implement your logic here
    return {"score": 0, "notes": "placeholder"}

# ----------------------------
# Client / LLM helpers
# ----------------------------
def _get_client() -> OpenAI:
    """
    Creates and returns an OpenAI client using OPENAI_API_KEY from env.
    """
    load_env()
    key = get_api_key()
    if not key:
        raise RuntimeError(
            "OPENAI_API_KEY not found. Put it in a .env file in the project root:\n"
            "OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx\n"
            "Or set it in your system environment variables."
        )
    return OpenAI(api_key=key)


def _chat(
    messages: List[Dict[str, str]],
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
) -> str:
    """
    Executes a chat completion and returns assistant text.
    """
    client = _get_client()
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    return (resp.choices[0].message.content or "").strip()


# ----------------------------
# Core features
# ----------------------------
def simulate_feedback(
    feature_description: str,
    persona: Dict[str, Any],
    model: str = "gpt-4o-mini",
) -> str:
    """
    Generates persona-specific feedback for a given feature description.
    Returns: feedback text (string)
    """
    prompt = build_user_prompt(feature_description, persona)

    messages = [
        {"role": "system", "content": SYSTEM_INSTRUCTIONS.strip()},
        {"role": "user", "content": prompt.strip()},
    ]

    return _chat(messages, model=model, temperature=0.7)


def analyze_feedback(
    feature_description: str,
    persona_outputs: List[Dict[str, Any]],
    model: str = "gpt-4o-mini",
) -> str:
    """
    Aggregates and analyzes feedback across multiple personas.
    persona_outputs expected format (each item):
      {
        "persona_name": str,
        "persona": dict,
        "feedback": str
      }
    Returns: analysis text (string)
    """
    prompt = build_analysis_prompt(feature_description, persona_outputs)

    messages = [
        {"role": "system", "content": "You are a product analyst. Be concise, structured, and actionable."},
        {"role": "user", "content": prompt.strip()},
    ]

    return _chat(messages, model=model, temperature=0.4)


def simulate_followup(
    feature_description: str,
    persona: Dict[str, Any],
    chat_history: List[Dict[str, str]],
    user_question: str,
    model: str = "gpt-4o-mini",
) -> str:
    """
    Continues a conversation as the selected persona.

    chat_history format:
      [{"role": "user"/"assistant", "content": "..."}]

    Returns: persona reply text (string)
    """
    prompt = build_followup_prompt(
        feature_description=feature_description,
        persona=persona,
        chat_history=chat_history,
        user_question=user_question,
    )

    messages = [
        {"role": "system", "content": SYSTEM_INSTRUCTIONS.strip()},
        {"role": "user", "content": prompt.strip()},
    ]

    return _chat(messages, model=model, temperature=0.7)
