"""Transparent backgrounds for AI image generation, solved from the same frame on white and on black.

    python matte.py white.png black.png out.png
    python matte.py white.png black.png out.png --pockets
"""

import argparse

import numpy as np
from PIL import Image, ImageFilter

# Cw - Cb = (1 - a) * 255. Exact where the model repainted the background, and no colour is keyed,
# so nothing in the art can be mistaken for background. Two renders agree to a few counts rather
# than exactly, so the ends are pulled flat.
SOLID, CLEAR = 0.85, 0.02

# The model leaves enclosed pockets white, between the legs or inside a grip, and those read as
# opaque because both renders agree there. Segmentation vetoes them. It only ever forces alpha to
# zero, never touches the boundary, so its own softness cannot reach the edge. Run at a reduced
# edge for the same reason: only the topology is used.
# isnet peaks at 1.3 GB against birefnet-general's 9 GB for the same background coverage.
POCKET = 240
VETO = "isnet-general-use"
VETO_EDGE = 512

# Eye whites, teeth and collars are enclosed white too, and segmentation calls them background.
# A gap is judged as a whole region, and only one larger than this share of the frame counts,
# which a figure's eyes and teeth never reach.
POCKET_MIN_AREA = 0.001

# The figure must be identical in both renders. A figure pixel that moved further than the solve
# tolerates was redrawn rather than kept, and its alpha is wrong. Pixels this close to the outline
# are skipped, since anti-aliased edges change between renders by design. Lines inside the figure
# still re-render a fraction of a pixel apart: the example pair reads 1.5% from those alone, and
# the same pair with the black render shifted by one pixel reads 4.6%.
DRIFT_TOLERANCE = (1 - SOLID) * 255
DRIFT_EDGE = 3
DRIFT_WARN = 0.03


def solve_alpha(lit: np.ndarray, dark: np.ndarray) -> np.ndarray:
    alpha = np.clip(1 - (lit - dark).mean(axis=2) / 255, 0, 1)
    alpha = np.where(alpha > SOLID, 1.0, alpha)
    return np.where(alpha < CLEAR, 0.0, alpha)


def drift(lit: np.ndarray, dark: np.ndarray) -> float:
    "Share of figure pixels, outline excluded, that changed between the two renders."
    background = (lit.min(axis=2) > POCKET) & (dark.max(axis=2) < 255 - POCKET)
    figure = Image.fromarray((~background).astype(np.uint8) * 255, "L")
    inside = np.array(figure.filter(ImageFilter.MinFilter(2 * DRIFT_EDGE + 1))) > 127
    if not inside.any():
        return 0.0
    changed = np.abs(lit - dark).mean(axis=2) > DRIFT_TOLERANCE
    return float(changed[inside].mean())


def gaps(white: Image.Image, lit: np.ndarray, dark: np.ndarray, session) -> np.ndarray:
    "Pixels of the see-through gaps: pocket regions large enough that segmentation calls mostly background."
    import rembg
    from scipy import ndimage

    # A pocket is white in both renders, which is exactly why the solve calls it opaque. Limiting
    # the veto to those pixels means a mis-segmented frame cannot eat the figure.
    pocket = (lit.min(axis=2) > POCKET) & (dark.min(axis=2) > POCKET)
    regions, count = ndimage.label(pocket)
    scale = VETO_EDGE / max(white.size)
    small = white.convert("RGB").resize((round(white.width * scale), round(white.height * scale)))
    mask = rembg.remove(small, session=session, only_mask=True).convert("L").resize(white.size)
    background = np.array(mask, dtype=float) / 255 < 0.5

    area = np.bincount(regions.ravel(), minlength=count + 1)
    background_share = np.bincount(regions.ravel(), weights=background.ravel(), minlength=count + 1) / np.maximum(area, 1)
    is_gap = (area >= POCKET_MIN_AREA * pocket.size) & (background_share > 0.5)
    is_gap[0] = False
    return is_gap[regions]


def matte(white: Image.Image, black: Image.Image, session=None) -> Image.Image:
    "Pass a rembg session to veto enclosed gaps. Leave it out for frames with nothing to see through."
    if white.size != black.size:
        raise ValueError(f"renders differ in size: {white.size} vs {black.size}")

    lit = np.array(white.convert("RGB"), dtype=float)
    dark = np.array(black.convert("RGB"), dtype=float)
    alpha = solve_alpha(lit, dark)
    if session is not None:
        alpha = np.where(gaps(white, lit, dark, session), 0.0, alpha)

    # Colour from the black render, so white spill cannot exist.
    colour = np.clip(dark / np.maximum(alpha, 1e-3)[:, :, None], 0, 255)
    return Image.fromarray(np.dstack([colour, alpha * 255]).astype(np.uint8), "RGBA")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("white", help="frame rendered on a white background")
    parser.add_argument("black", help="the same frame rendered on a black background")
    parser.add_argument("out", help="RGBA png to write")
    parser.add_argument("--pockets", action="store_true", help="veto enclosed see-through gaps, needs rembg")
    args = parser.parse_args()

    session = None
    if args.pockets:
        import rembg

        session = rembg.new_session(VETO)

    white, black = Image.open(args.white), Image.open(args.black)
    result = matte(white, black, session)
    result.save(args.out)

    alpha = np.array(result)[:, :, 3]
    moved = drift(np.array(white.convert("RGB"), dtype=float), np.array(black.convert("RGB"), dtype=float))
    print(
        f"clear={100 * (alpha == 0).mean():.1f}%  partial={100 * ((alpha > 0) & (alpha < 255)).mean():.2f}%"
        f"  drift={100 * moved:.2f}%"
    )
    if moved > DRIFT_WARN:
        print("warning: the figure changed between the renders, so its alpha is wrong. See Drift in the README.")


if __name__ == "__main__":
    main()
