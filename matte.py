"""Transparent backgrounds for AI image generation, solved from the same frame on white and on black.

    python matte.py white.png black.png out.png
    python matte.py white.png black.png out.png --pockets
"""

import argparse

import numpy as np
from PIL import Image

# Cw - Cb = (1 - a) * 255. Exact where the model repainted the background, and no colour is keyed,
# so nothing in the art can be mistaken for background. Two renders agree to a few counts rather
# than exactly, so the ends are pulled flat.
SOLID, CLEAR = 0.85, 0.02


def solve_alpha(lit: np.ndarray, dark: np.ndarray) -> np.ndarray:
    alpha = np.clip(1 - (lit - dark).mean(axis=2) / 255, 0, 1)
    alpha = np.where(alpha > SOLID, 1.0, alpha)
    return np.where(alpha < CLEAR, 0.0, alpha)


def matte(white: Image.Image, black: Image.Image) -> Image.Image:
    if white.size != black.size:
        raise ValueError(f"renders differ in size: {white.size} vs {black.size}")

    lit = np.array(white.convert("RGB"), dtype=float)
    dark = np.array(black.convert("RGB"), dtype=float)
    alpha = solve_alpha(lit, dark)

    # Colour from the black render, so white spill cannot exist.
    colour = np.clip(dark / np.maximum(alpha, 1e-3)[:, :, None], 0, 255)
    return Image.fromarray(np.dstack([colour, alpha * 255]).astype(np.uint8), "RGBA")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("white", help="frame rendered on a white background")
    parser.add_argument("black", help="the same frame rendered on a black background")
    parser.add_argument("out", help="RGBA png to write")
    args = parser.parse_args()

    result = matte(Image.open(args.white), Image.open(args.black))
    result.save(args.out)

    alpha = np.array(result)[:, :, 3]
    print(f"clear={100 * (alpha == 0).mean():.1f}%  partial={100 * ((alpha > 0) & (alpha < 255)).mean():.2f}%")


if __name__ == "__main__":
    main()
