"""Renders a known RGBA figure onto white and black, mattes the pair, and compares.

    python test_matte.py
"""

import numpy as np
from PIL import Image

from matte import DRIFT_WARN, drift, matte

SIZE = 64


def figure() -> np.ndarray:
    "Dark body, a white eye drawn inside it, and a half transparent rim."
    rgba = np.zeros((SIZE, SIZE, 4), dtype=float)
    rgba[16:48, 16:48] = (60, 40, 30, 255)
    rgba[24:30, 24:30] = (255, 255, 255, 255)
    rgba[14:16, 16:48] = (60, 40, 30, 128)
    return rgba


def render(rgba: np.ndarray, background: int) -> Image.Image:
    alpha = rgba[:, :, 3:] / 255
    flat = rgba[:, :, :3] * alpha + background * (1 - alpha)
    return Image.fromarray(np.round(flat).astype(np.uint8), "RGB")


def main() -> None:
    truth = figure()
    result = np.array(matte(render(truth, 255), render(truth, 0)), dtype=float)

    assert (result[26, 26] == (255, 255, 255, 255)).all(), "white eye must stay opaque and white"
    assert (result[32, 32] == (60, 40, 30, 255)).all(), "body must stay opaque"
    assert abs(result[15, 32, 3] - 128) <= 1, "rim must keep its partial alpha"
    assert abs(result[15, 32, :3] - (60, 40, 30)).max() <= 2, "rim colour must carry no white spill"
    assert result[2, 2, 3] == 0, "background must be clear"

    lit = np.array(render(truth, 255), dtype=float)
    dark = np.array(render(truth, 0), dtype=float)
    assert drift(lit, dark) == 0, "an unchanged figure must show no drift"
    redrawn = dark.copy()
    redrawn[20:44, 20:44] = (110, 90, 80)
    assert drift(lit, redrawn) > DRIFT_WARN, "a figure redrawn in the black render must warn"
    print("ok")


if __name__ == "__main__":
    main()
