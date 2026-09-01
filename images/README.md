# Photos

Drop the real photos here with exactly these filenames. Any file that is missing
falls back to a dark placeholder tile on the page — nothing breaks, the tile just
shows the expected filename.

| Path | Aspect | Suggested size | Used for |
|---|---|---|---|
| `hero.jpg` | 4:3 | 1200×900 | Hero photo, first screen |
| `why.jpg` | 5:6 (portrait) | 900×1080 | "Dlaczego Hot Tub Elite" section |
| `og.jpg` | 1.91:1 | 1200×630 | Social media link preview |
| `apple-touch-icon.png` | 1:1 | 180×180 | iOS home-screen icon |
| `models/5r50-1.jpg`, `-2.jpg` | 4:3 | 1200×900 | Model 5R50 slider |
| `models/6r02-1.jpg`, `-2.jpg` | 4:3 | 1200×900 | Model 6R02 slider |
| `models/5a13-1.jpg`, `-2.jpg` | 4:3 | 1200×900 | Model 5A13 slider |
| `piec/piec-1.jpg`, `-2.jpg` | 2:1 | 1200×600 | Wood stove section |
| `gallery/01.jpg` … | 4:3 | 1200×900 | Realisations gallery |

Sizes are what `place-photos.py` produces; it crops and resizes from `inbox/`, so
drop originals there rather than editing these files directly.

## One photo, one place

No photo appears in two sections. A gallery that repeats the sliders above it reads
as padding, and a visitor who notices spots it immediately. `place-photos.py` maps
each source to exactly one slot — keep it that way when adding photos.

## Section sizes follow the photo count

The sliders take however many slides the HTML contains (the dots are generated from
that), the stove section takes two, and the gallery count is `CONFIG.galleryCount`
in `index.html`. The gallery grid is three columns with one 2×2 feature tile, so it
fills exactly when the tile count is a multiple of three — 6, 9, 12.

## Before committing

Compress every photo. Uncompressed camera JPEGs will make the page slow on mobile
and eat the GitHub Pages bandwidth budget.

```bash
# ImageMagick — resize to max 1400px wide and re-encode at quality 82
mogrify -resize '1400x1400>' -quality 82 -strip images/**/*.jpg
```

Target: under 250 KB per photo, ideally under 150 KB.

## Changing the gallery photo count

The gallery is generated in `index.html` from `CONFIG.galleryCount`. Change that one
number and add/remove files named `01.jpg`, `02.jpg`, … to match.
