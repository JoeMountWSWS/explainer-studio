# Licensed fonts

Commercial fonts the studio uses when they're present. Everything here except this README is
gitignored: the repo is public and `brand/fonts/` ships in the PyPI wheel, so these must never be
committed or moved there.

`studio sync` copies these into each episode's `assets/brand/fonts/` and appends their `@font-face`
rules to the episode's copy of `brand.css`, whose `--font-sans` puts
DINPro at the front of `--font-sans`. Without them, the sans text falls back to Source Sans 3.

| File | Weight |
| --- | --- |
| `DINPro-Light.ttf` | 300 |
| `DINPro-Medium.ttf` | 500 (also used for 400) |
| `DINPro-Bold.ttf` | 700 (also used for 600, and for burned-in captions) |
| `DINPro-Black.ttf` | 900 |

DINPro is © Albert-Jan Pool / FSI FontShop International (FontFont, now Monotype); EULA at
fontfont.com/eula. Rendering it into videos and images is fine; redistributing the files isn't.
To set up a new checkout, unzip `DINPro.zip` here, dropping the " tr" suffix from the file names
(`DINPro-Bold tr.ttf` → `DINPro-Bold.ttf`).
