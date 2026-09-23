import numpy as np

from visor.geometry import estimate_homography
from visor.matching import match_features
from visor.models import DescriptorInfo, FeatureSet, KeypointInfo, MatchInfo, MatchSet


def _feature_set(points, descriptors=None):
    keypoints = tuple(KeypointInfo(float(x), float(y), 8.0, 0.0, 1.0, 0, -1) for x, y in points)
    desc = descriptors
    info = DescriptorInfo(len(keypoints), 2, "FLOAT32", 0 if desc is None else desc.nbytes, "L2")
    return FeatureSet(keypoints, desc, info, 0.0)


def test_ratio_matcher_rejects_ambiguous_neighbors():
    reference = _feature_set([(0, 0)], np.array([[0.0, 0.0]], dtype=np.float32))
    target_desc = np.array([[0.0, 0.0], [0.0, 0.0], [3.0, 3.0]], dtype=np.float32)
    target = _feature_set([(0, 0), (1, 1), (2, 2)], target_desc)
    result = match_features(reference, target, "SIFT", ratio_threshold=0.75)
    assert result.candidate_count == 1
    assert result.good_count == 0


def test_homography_projects_planar_reference_corners():
    source = [(10, 10), (100, 10), (100, 80), (10, 80), (50, 40), (70, 55)]
    target = [tuple(p) for p in (np.asarray(source) + np.array([23, 17]))]
    ref_set, target_set = _feature_set(source), _feature_set(target)
    matches = MatchSet(tuple(MatchInfo(i, i, 1.0, 0.1) for i in range(len(source))), len(source), len(source), "BF/L2", "ratio", 0.75, 0.0)
    result, elapsed = estimate_homography(ref_set, target_set, matches, (120, 100))
    assert result.valid
    assert result.inlier_count == len(source)
    assert result.center is not None
    assert abs(result.projected_corners[0][0] - 23) < 1e-2
    assert abs(result.projected_corners[0][1] - 17) < 1e-2
    assert elapsed >= 0


def test_homography_rejects_too_few_correspondences():
    ref_set, target_set = _feature_set([(0, 0)] * 3), _feature_set([(1, 1)] * 3)
    matches = MatchSet(tuple(MatchInfo(i, i, 1.0, 0.1) for i in range(3)), 3, 3, "BF/L2", "ratio", 0.75, 0.0)
    result, _ = estimate_homography(ref_set, target_set, matches, (100, 100))
    assert not result.valid
    assert result.homography is None


def test_homography_reports_reference_completely_outside_target():
    source = [(10, 10), (100, 10), (100, 80), (10, 80), (50, 40), (70, 55)]
    target = [(x + 500, y + 500) for x, y in source]
    ref_set, target_set = _feature_set(source), _feature_set(target)
    matches = MatchSet(tuple(MatchInfo(i, i, 1.0, 0.1) for i in range(len(source))), len(source), len(source), "BF/L2", "ratio", 0.75, 0.0)
    result, _ = estimate_homography(ref_set, target_set, matches, (120, 100), target_size=(100, 100))
    assert not result.valid
    assert "outside" in result.message


def test_invalid_ratio_threshold_fails_clearly():
    features = _feature_set([], None)
    try:
        match_features(features, features, "SIFT", ratio_threshold=1.0)
    except ValueError as exc:
        assert "Ratio threshold" in str(exc)
    else:
        raise AssertionError("invalid ratio threshold should be rejected")


def test_engine_settings_reject_invalid_numeric_values():
    from visor.engines import ORBConfiguration, SIFTConfiguration
    from visor.models import AnalysisSettings

    for factory in (
        lambda: AnalysisSettings(ransac_threshold=0),
        lambda: SIFTConfiguration(sigma=float("nan")),
        lambda: ORBConfiguration(scale_factor=1.0),
    ):
        try:
            factory()
        except ValueError:
            pass
        else:
            raise AssertionError("invalid algorithm settings should be rejected")
