import pytest
from pathlib import Path
from backend.app.utils.file_validator import validate_file


def test_valid_geotiff():
    path = "./sample_data/sample_optical_hyderabad.tif"
    is_valid, msg, meta = validate_file(path)
    assert is_valid is True
    assert meta["bands"] == 3
    assert meta["width"] == 512
    assert meta["height"] == 512


def test_unsupported_extension(tmp_path):
    fake_png = tmp_path / "satellite.png"
    fake_png.write_text("not a geotiff")
    is_valid, msg, meta = validate_file(str(fake_png))
    assert is_valid is False
    assert "Unsupported file type" in msg


def test_corrupted_tif(tmp_path):
    corrupt = tmp_path / "corrupt.tif"
    corrupt.write_bytes(b"corrupted binary data that is not a real tiff header")
    is_valid, msg, meta = validate_file(str(corrupt))
    assert is_valid is False
    assert "not a valid GeoTIFF" in msg
