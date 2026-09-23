import cv2
import numpy as np

from visor.engines import ORBConfiguration, ORBFeatureEngine, SIFTFeatureEngine


def test_sift_exposes_float_descriptors_and_keypoint_metadata():
    image = np.zeros((160, 160), dtype=np.uint8)
    cv2.putText(image, "VISOR", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1.7, 255, 3)
    result = SIFTFeatureEngine().extract(image)
    assert result.descriptor_info.distance == "L2"
    assert result.descriptor_info.dimensions == 128
    assert result.descriptor_info.dtype == "FLOAT32"
    assert result.descriptor_info.count == len(result.keypoints)
    assert result.extraction_ms >= 0
    if result.keypoints:
        assert result.keypoints[0].size > 0


def test_orb_hamming2_tracks_wta_configuration():
    image = np.random.default_rng(4).integers(0, 256, (180, 180), dtype=np.uint8)
    result = ORBFeatureEngine(ORBConfiguration(wta_k=4)).extract(image)
    assert result.descriptor_info.dimensions == 32
    assert result.descriptor_info.distance == "HAMMING2"
    assert result.descriptor_info.dtype == "UINT8 / BINARY"


def test_orb_rejects_unsupported_wta():
    image = np.zeros((80, 80), dtype=np.uint8)
    try:
        ORBFeatureEngine(ORBConfiguration(wta_k=5)).extract(image)
    except ValueError as exc:
        assert "WTA_K" in str(exc)
    else:
        raise AssertionError("invalid WTA_K should be rejected")
