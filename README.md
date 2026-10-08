# ai-alpha-bg

Transparent backgrounds for AI generated images, solved from the same frame rendered on white and on black.

## Usage

```
pip install -r requirements.txt
python matte.py white.png black.png out.png
python matte.py white.png black.png out.png --pockets
```

`--pockets` makes enclosed gaps transparent, such as the space between the legs or inside a bent arm. Use it for full figures only. Portraits have nothing to see through, so leave it off there.

## Getting the pair

1. Generate the frame on white as usual.
2. Pass that frame back to an image editing model as the reference, with the prompt `the same subject, unchanged, on a solid black background`.

Two renders at a fixed seed are not pixel identical, so the black frame has to reference its own white frame rather than share a seed with it.

## How it works

- **Alpha** from the pair: `a = 1 - (Cw - Cb) / 255`, with values above 0.85 pulled to opaque and below 0.02 to clear, since the two renders agree to a few counts rather than exactly.
- **Colour** from the black render: `F = Cb / a`. No white spill on the edges.
- No colour is keyed, so white eyes, teeth and pale cloth stay opaque.
- **Pockets.** The model leaves enclosed gaps white in both renders, and the solve reads white in both as opaque. With `--pockets`, segmentation (`isnet-general-use` at 512px) makes them clear. It only touches regions that are near white in both renders and larger than 0.1% of the frame, and only when segmentation calls most of the region background. It never touches the figure's edge. Without the size limit it cut holes into eye whites and collars.

The formula is triangulation matting, Smith and Blinn, *Blue Screen Matting*, SIGGRAPH 1996.

## Tried first

- Keying white: eyes, pale cloth and the background are the same white.
- Border flood fill: enclosed pockets stay opaque.
- BiRefNet: right shape, thin white edge.
- `1 - max(RGB)` as alpha: assumes a black outline, so bright edges turn transparent.
- InSPyReNet: cleanest edges, but it punches out the eyes and misses the gap under a raised arm.
- Prompting the model to fill pockets with black: three phrasings, identical output.

## Open

Enclosed pockets without segmentation.

## Test

```
python test_matte.py
```
