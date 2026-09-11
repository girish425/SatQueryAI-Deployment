import pytest
from backend.app.agent.intent_classifier import intent_classifier


def test_intent_image_understanding():
    res1 = intent_classifier.classify("What is visible in this image?")
    assert res1["intent"] == "image_understanding"
    assert res1["confidence"] > 0.6

    res2 = intent_classifier.classify("Describe the image.")
    assert res2["intent"] == "image_understanding"

    res3 = intent_classifier.classify("What type of land cover is present?")
    assert res3["intent"] == "image_understanding"


def test_intent_vqa_presence():
    res1 = intent_classifier.classify("Is there water in this image?")
    assert res1["intent"] == "vqa"

    res2 = intent_classifier.classify("Are there buildings?")
    assert res2["intent"] == "vqa"

    res3 = intent_classifier.classify("What crops are visible in this image?")
    assert res3["intent"] == "vqa"


def test_intent_grounding():
    res1 = intent_classifier.classify("Where is the river?")
    assert res1["intent"] == "grounding"

    res2 = intent_classifier.classify("Highlight the road.")
    assert res2["intent"] == "grounding"

    res3 = intent_classifier.classify("Locate the vegetation.")
    assert res3["intent"] == "grounding"


def test_intent_change_detection():
    res1 = intent_classifier.classify("What changed between these images?", num_images=2)
    assert res1["intent"] == "change_detection"

    res2 = intent_classifier.classify("Compare these images.", num_images=2)
    assert res2["intent"] == "change_detection"

    res3 = intent_classifier.classify("What increased or decreased between the dates?", num_images=2)
    assert res3["intent"] == "change_detection"


def test_intent_optical_sar():
    res1 = intent_classifier.classify("Analyze the optical and SAR images together.")
    assert res1["intent"] == "optical_sar"

    res2 = intent_classifier.classify("Compare radar and optical information.")
    assert res2["intent"] == "optical_sar"
