# Platformer Animated Collectibles

An original MakeCode Arcade asset pack with **12 collectible families**, each containing:

- a ready-to-use **static image** for creating the collectible sprite;
- a compact **4-frame idle loop**;
- a custom **4-frame collected one-shot**; and
- exact 16×16 artwork using Arcade's default palette.

![Animated preview](collectibles-preview.gif)

Included collectibles: spinning coin, energy orb, crystal, star, heart, key, potion, berries, gear, energy cell, crown, and wrapped candy.

## Use in MakeCode Arcade

1. Open a game in [MakeCode Arcade](https://arcade.makecode.com/).
2. Open **Settings → Extensions**.
3. Paste `https://github.com/mrbrackebusch-code/PlatformerCollectibles` into the search box.
4. Select the extension card.
5. Create each collectible sprite with its plainly named image asset, such as `Coin`, `Heart`, or `Potion`.
6. Open the Animation editor to find the matching idle and collected animations.

This is an art-only extension: it adds no gameplay behavior. Its generated lookup code keeps gallery selections and named image or animation references on the same resources, including identifiers already used by v0.0.2 projects.

Each static image is identical to the first frame of its idle animation, so starting the animation does not cause a visual jump.

For each item, choose the matching `Idle` and `Collected` animations. Loop the idle animation. Run the collected animation once, then destroy or hide the collectible after the final frame. Each collected sequence preserves the item's identity: coins flip away, orbs contract, crystals split into shards, hearts release tiny hearts, potions pop into bubbles, batteries discharge, and candies unwrap into sugar sparkles. No stock destroyed effect is needed.

Suggested timing is recorded in `animation-manifest.json`. Idle loops use 120–170 ms per frame; collected animations use 75 ms per frame and should not loop.

## Contents

- `images.g.jres` / `images.g.ts`: MakeCode image and animation assets
- `test.ts`: compile-only resolution check for all 12 images and 24 animations
- `contact-sheet.png`: every exact frame at readable scale
- `collectibles-preview.gif`: simple montage of every idle and collected animation
- `previews/`: one animated preview per collectible
- `frames/`: every source frame as a lossless PNG
- `ANIMATION_ASCII.md`: exact palette-index pixels
- `animation-manifest.json`: dimensions, timing, hashes, and validation facts
- `build_collectibles.py`: deterministic source generator

## License

MIT. These assets may be used, changed, and redistributed in student projects and tutorials under the terms in `LICENSE`.
