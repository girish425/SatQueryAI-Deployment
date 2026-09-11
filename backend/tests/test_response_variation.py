import pytest
from pathlib import Path
from backend.app.agent.controller import agent_controller


def test_five_questions_produce_distinct_responses():
    image_path = "./sample_data/sample_optical_hyderabad.tif"
    assert Path(image_path).exists(), "Sample optical GeoTIFF must exist"

    questions = [
        "What is visible in this image?",
        "Is there water?",
        "Are there buildings?",
        "Where is the river?",
        "Describe the image."
    ]

    responses = []
    summaries = []
    intents = []
    models_used = []

    for q in questions:
        resp = agent_controller.process_query(
            query=q,
            image_paths=[image_path],
            session_id="test_variation_session"
        )
        responses.append(resp)
        summaries.append(resp["answer"]["summary"])
        intents.append(resp["intent"])
        models_used.append(resp["model_used"])

    # 1. Verify intents change when appropriate
    assert "image_understanding" in intents
    assert "vqa" in intents
    assert "grounding" in intents

    # 2. Verify answers are not identical
    # Every question must yield a unique summary!
    assert len(set(summaries)) == len(questions), f"Summaries must all be distinct! Found duplicates in {summaries}"

    # 3. Check question-relevant content
    # "Is there water?" response should mention water
    q_water_resp = responses[1]
    assert "water" in q_water_resp["answer"]["summary"].lower()

    # "Are there buildings?" response should mention building or structure
    q_bld_resp = responses[2]
    assert any(w in q_bld_resp["answer"]["summary"].lower() for w in ["building", "structure", "built-up"])

    # "Where is the river?" response should mention river and grounding
    q_river_resp = responses[3]
    assert "river" in q_river_resp["answer"]["summary"].lower()
    assert q_river_resp["intent"] == "grounding"
