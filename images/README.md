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
| `models/5r50-1.jpg` … `-3.jpg` | 4:3 | 900×675 | Model 5R50 slider |
| `models/6r02-1.jpg` … `-3.jpg` | 4:3 | 900×675 | Model 6R02 slider |
| `models/5a13-1.jpg` … `-3.jpg` | 4:3 | 900×675 | Model 5A13 slider |
| `gallery/01.jpg` … `12.jpg` | 4:3 | 1000×750 | Realisations gallery |
| `piec/piec-1.jpg` | 4:3 | 1000×750 | Wood stove — wide shot next to the tub |
| `piec/piec-2.jpg` | 1:1 | 800×800 | Wood stove — firebox lit |
| `piec/piec-3.jpg` | 1:1 | 800×800 | Tub with the stove chimney, in a garden |
| `reviews/1.jpg` … `3.jpg` | 4:3 | 900×675 | Customer photo on each review card |

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
