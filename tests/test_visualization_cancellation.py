"""Pure rendering checks cooperative cancellation without publishing partial buffers."""

from dataclasses import replace

import numpy as np
import pytest

from visor.pipeline import analyze
from visor.visualization import render_localization, render_match_canvas


@pytest.mark.parametrize("kind", ["matches", "localization"])
def test_overlay_cancels_during_drawing_without_mutating_inputs(textured_pair, kind):
    result = analyze(*textured_pair[:2], "ORB")
    before = result.target_image.copy()
    calls = []

    def cancel():
        calls.append(1)
        if len(calls) == 3:
            raise RuntimeError("cancelled fixture")

    settings = replace(result.settings, show_keypoints=True)
    with pytest.raises(RuntimeError, match="cancelled fixture"):
        if kind == "matches":
            render_match_canvas(result.reference_image, result.target_image, result.reference_features,
                                result.target_features, result.match_set, result.geometry, settings, cancel_check=cancel)
        else:
            render_localization(result.target_image, result.target_features, result.geometry, settings, cancel_check=cancel)
    assert len(calls) == 3
    np.testing.assert_array_equal(result.target_image, before)
