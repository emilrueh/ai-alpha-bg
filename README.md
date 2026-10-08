# ai-alpha-bg

<p>
  <img src="example/white.png" width="32%" alt="Cartoon chef generated on white">
  <img src="example/black.png" width="32%" alt="The same chef repainted on black">
  <picture>
    <source media="(prefers-color-scheme: light)" srcset="example/alpha_checker.png">
    <img src="example/alpha.png" width="32%" alt="The chef with a transparent background">
  </picture>
</p>

Most image models can't output transparent backgrounds. The ones that can, like LayerDiffuse for SD1.5 and SDXL or hosted models with a transparency option, can't run your own LoRA on a current base model. And cutting the figure out of a white background breaks wherever the figure itself is white: eyes, teeth, pale cloth.

This tool takes a different route. You give it two images of the same figure, one on white and one on black. Comparing them shows exactly how much background is behind every pixel:

- **Part of the figure:** looks the same in both images, so it is opaque.
- **Background:** white in one, black in the other, so it is transparent.
- **In between,** like soft edges and hair: partly transparent, by exactly how much it changed.

No colour is treated as background, so white parts of the figure stay opaque, like the chef's hat, jacket and teeth above.

The tool does the comparison. Making the two images is up to your image model, see [Making the black image](#making-the-black-image).

## Usage

```
pip install -r requirements.txt
python matte.py white.png black.png out.png
python matte.py example/white.png example/black.png out.png
python test_matte.py
```

Every run prints how much of the image came out clear, partly transparent, and how much the figure drifted between the two images.

## Steps

1. **Generate the image on a white background**, as usual.
2. **Generate the black image from the white one.** The figure must stay identical, only the background changes. See below.
3. **Solve transparency** from the pair: `alpha = 1 - (white - black) / 255`. The two images still differ by a few values where they should match, so values close to fully opaque or fully clear are rounded to it.
4. **Take the colour from the black image,** divided by its transparency. Taking it from the white one would leave a white fringe on soft edges.

Step 3 is triangulation matting, from Smith and Blinn, *Blue Screen Matting*, SIGGRAPH 1996.

## Making the black image

Everything depends on this step. The black image must show the same figure as the white one, pixel for pixel, with only the background changed. Two ways to get there:

- **Works:** pass the white image to the model as a reference image and ask for the same thing on black, with the prompt `the same subject, unchanged, on a solid black background`.
- **Does not work:** generating the black image separately with the same prompt and seed. Even a fixed seed gives slightly different images, and every pixel that moved comes out wrong.

**Tested with** FLUX.2 klein 4B, the white image as its reference image, the prompt above, and a style LoRA at 0.4 strength. A strong LoRA can redraw the figure instead of keeping it, so keep the strength low for this step.

**Not tested** with other editing models. Models that redraw the whole image rather than edit it, which includes most hosted editors, are likely to move the figure. The drift check tells you.

## Drift check

Every run measures how many figure pixels changed between the two images, skipping the outline, where small changes are expected.

- **Clean pair:** around 1 to 2%, from lines inside the figure landing a fraction of a pixel apart. The example reads 1.5%.
- **Warning above 3%:** the figure moved or was redrawn, and its transparency is wrong where it did. The example with the black image shifted by one pixel already reads 4.6%.

If it warns, lower the LoRA strength for the black image, or try a model that edits rather than redraws.

## Enclosed gaps, `--pockets`

```
python matte.py white.png black.png out.png --pockets
```

The model often doesn't repaint background it sees as enclosed, like the gap between the legs or inside a bent arm. Those areas stay white in the black image too, so the comparison sees no change and keeps them opaque.

`--pockets` clears them using a second model, the background remover `isnet-general-use` through `rembg`. It downloads on first use and needs the extra packages in `requirements.txt`. To keep that model from damaging the figure:

- It only clears areas that are white in both images. It never changes edges or anything coloured.
- It only clears an area as a whole, and only if the area is larger than 0.1% of the image and the model calls most of it background.

That size rule protects eyes and teeth in full figures, where they are small. In a close-up they can pass it, so leave `--pockets` off for portraits.
