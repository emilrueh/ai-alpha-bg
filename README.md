# ai-alpha-bg

Image models can't output transparent backgrounds, and cutting the figure out of a white background breaks wherever the figure itself is white: eyes, teeth, pale cloth.

This tool takes a different route. Generate the image on white, then have the model repaint the same image on black. Comparing the two shows exactly how much background is behind every pixel:

- **Part of the figure:** looks the same in both images, so it is opaque.
- **Background:** white in one, black in the other, so it is transparent.
- **In between,** like soft edges and hair: partly transparent, by exactly how much it changed.

No colour is treated as background, so white eyes stay white.

## Steps

1. **Generate the image on a white background**, as usual.
2. **Generate the black version from the white one.** Pass the white image to an image editing model as the reference, with the prompt `the same subject, unchanged, on a solid black background`. The reference is what makes this work: both images must show the identical figure, pixel for pixel. Generating twice with the same seed is not enough, since even a fixed seed gives slightly different images.
3. **Solve transparency** from the pair: `alpha = 1 - (white - black) / 255`. The two images still differ by a few values where they should match, so values close to fully opaque or fully clear are rounded to it.
4. **Take the colour from the black image,** divided by its transparency. Taking it from the white one would leave a white fringe on soft edges.
5. **Optional, `--pockets`:** clear see-through gaps such as the space between the legs. The model often leaves them white in the black image too, so step 3 sees no change there and keeps them opaque. A background removal model (`isnet-general-use`) finds them. Only white areas larger than 0.1% of the image count, so eyes and teeth are never cut. Use it for full figures, not portraits.

## Usage

```
pip install -r requirements.txt
python matte.py white.png black.png out.png
python matte.py white.png black.png out.png --pockets
python test_matte.py
```

Step 3 is triangulation matting, from Smith and Blinn, *Blue Screen Matting*, SIGGRAPH 1996.
