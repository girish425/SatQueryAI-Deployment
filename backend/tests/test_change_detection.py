import pytest
from backend.app.models.change_detection import change_detection_model


def test_change_detection_different_images():
    t1 = "./sample_data/sample_change_t1.tif"
    t2 = "./sample_data/sample_change_t2.tif"

    res = change_detection_model.analyze([t1, t2])
    assert "change_percentage" in res
    assert res["change_percentage"] > 1.0
    assert len(res["answer"]["key_findings"]) >= 3
    assert res["evidence"]["difference_image"] is not None


def test_change_detection_identical_images():
    t1 = "./sample_data/sample_change_t1.tif"
    res = change_detection_model.analyze([t1, t1])
    assert res["change_percentage"] < 0.1


def test_change_detection_missing_second_image():
    t1 = "./sample_data/sample_change_t1.tif"
    with pytest.raises(ValueError) as exc:
        change_detection_model.analyze([t1])
    assert "Change detection requires two images" in str(exc.value)
