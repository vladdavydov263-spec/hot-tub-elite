#!/usr/bin/env python3
"""
Place photos from images/inbox into their final slots.

Sources are phone shots in mixed orientations; the slots on the page have fixed
aspect ratios. Cropping here (rather than leaning on object-fit alone) keeps the
subject in frame instead of letting a centred cover-crop slice the tub in half.

`focal` is the vertical centre of the crop as a fraction of source height —
0.5 is centred, higher moves the crop window down.

Re-run after changing images/inbox:

    python3 place-photos.py && python3 build-preview.py
"""

import pathlib
from PIL import Image, ImageOps

ROOT = pathlib.Path(__file__).parent
INBOX = ROOT / 'images' / 'inbox'

# Source files, in the order the contact sheet numbers them.
SRC = sorted(INBOX.rglob('*.jpg'))

# slot -> (source index, target aspect w/h or None to only resize, focal, long edge)
PLAN = {
    # Every source photo is used exactly once. There are 16 distinct shots and the
    # page has room for more, so sections are sized to the photos rather than the
    # photos stretched across the sections — a gallery that repeats the sliders
    # above it reads as padding.

    'hero.jpg':               (12, 4 / 3,  0.62, 1400),   # garden, cover open
    'why.jpg':                (19, 5 / 6,  0.50, 1080),   # lake and mountains

    # Model sliders: two shots each — a full view and a detail.
    'models/5r50-1.jpg':      (16, 4 / 3,  0.55, 1200),   # on the pallet
    'models/5r50-2.jpg':      (18, 4 / 3,  0.50, 1200),   # interior, from above

    'models/6r02-1.jpg':      (13, 4 / 3,  0.50, 1200),   # jets running, chimney
    'models/6r02-2.jpg':      (14, 4 / 3,  0.55, 1200),   # still water at sunset

    'models/5a13-1.jpg':      (1,  4 / 3,  0.50, 1200),   # cover open, on the pallet
    'models/5a13-2.jpg':      (0,  4 / 3,  0.50, 1200),   # interior, from above

    # Wood stove: the two shots that actually show the stove.
    'piec/piec-1.jpg':        (6,  2 / 1,  0.52, 1200),   # hooked up beside the tub
    'piec/piec-2.jpg':        (7,  2 / 1,  0.42, 1200),   # firebox, lit

    # Gallery: installed tubs, none of which appear anywhere else on the page.
    'gallery/01.jpg':         (4,  3 / 2,  0.50, 1300),   # dusk, with the steps
    'gallery/02.jpg':         (8,  None,   0.50, 1200),   # blue light, at night
    'gallery/03.jpg':         (17, None,   0.50, 1200),   # beside the ivy wall
    'gallery/04.jpg':         (5,  None,   0.50, 1200),   # open field, chimney
    'gallery/05.jpg':         (10, None,   0.50, 1200),   # covered, on the yard
    'gallery/06.jpg':         (11, None,   0.50, 1200),   # interior, close
}


def crop_to_aspect(im: Image.Image, aspect: float, focal: float) -> Image.Image:
    w, h = im.size
    if w / h > aspect:                      # too wide — trim the sides
        new_w = round(h * aspect)
        left = (w - new_w) // 2
        return im.crop((left, 0, left + new_w, h))
    new_h = round(w / aspect)               # too tall — trim vertically, around the focal point
    top = round(h * focal - new_h / 2)
    top = max(0, min(top, h - new_h))
    return im.crop((0, top, w, top + new_h))


def main() -> None:
    for slot, (idx, aspect, focal, long_edge) in PLAN.items():
        src = SRC[idx]
        im = Image.open(src)
        im = ImageOps.exif_transpose(im).convert('RGB')   # honour camera rotation
        if aspect:
            im = crop_to_aspect(im, aspect, focal)
        im.thumbnail((long_edge, long_edge), Image.LANCZOS)

        dst = ROOT / 'images' / slot
        dst.parent.mkdir(parents=True, exist_ok=True)
        im.save(dst, 'JPEG', quality=82, optimize=True, progressive=True)
        print(f'{slot:22s} <- {idx:02d} {src.parent.name:8s} '
              f'{im.width}x{im.height}  {dst.stat().st_size // 1024} KB')


if __name__ == '__main__':
    main()
