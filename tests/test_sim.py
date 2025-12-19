from pathlib import Path
from src.utility import load_personas
from src.prompts import build_user_prompt

def test_personas_load():
    data = load_personas()
    assert "personas" in data
    assert len(data["personas"]) >= 1

def test_build_prompt_contains_feature_and_persona():
    data = load_personas()
    persona = data["personas"][0]
    feature = "New iOS button that adds items to favorites."
    prompt = build_user_prompt(feature, persona)
    assert feature in prompt
    assert persona["name"] in prompt
def test_simulator_import():
    from src.simulator import simulate_feedback

def test_personas_load():
    personas = load_personas(PERSONAS_PATH)
    assert isinstance(personas, list)
    assert len(personas) >= 2
    assert "name" in personas[0]

def test_prompt_builds():
    personas = load_personas(PERSONAS_PATH)
    p = personas[0]
    prompt = build_simulation_prompt("Add a new button to the homepage.", p)
    assert "Feature to evaluate" in prompt
    assert p["name"] in prompt