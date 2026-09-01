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
    # first screen — portrait garden shot into a 4:3 frame, biased down onto the tub
    'hero.jpg':               (12, 4 / 3,  0.62, 1400),
    # "Dlaczego" — the 5:6 portrait slot
    'why.jpg':                (19, 5 / 6,  0.50, 1080),

    'models/6r02-1.jpg':      (13, 4 / 3,  0.50, 1200),
    'models/6r02-2.jpg':      (14, 4 / 3,  0.55, 1200),
    'models/6r02-3.jpg':      (15, 4 / 3,  0.50, 1200),

    'models/5a13-1.jpg':      (16, 4 / 3,  0.55, 1200),
    'models/5a13-2.jpg':      (17, 4 / 3,  0.55, 1200),
    'models/5a13-3.jpg':      (18, 4 / 3,  0.50, 1200),

    # wood stove — pulled out of the gallery batch, where these three had landed
    'piec/piec-1.jpg':        (6,  2 / 1,  0.52, 1200),   # stove hooked up beside the tub
    'piec/piec-2.jpg':        (7,  1 / 1,  0.46, 900),    # firebox, lit
    'piec/piec-3.jpg':        (3,  1 / 1,  0.55, 900),    # tub with the chimney, in a field

    # customer photos on the review cards
    'reviews/1.jpg':          (20, 4 / 3,  0.50, 900),
    'reviews/2.jpg':          (21, 4 / 3,  0.50, 900),
    'reviews/3.jpg':          (22, 4 / 3,  0.50, 900),

    # gallery — object-fit handles the tile shapes, so resize only, except the
    # opening 2x2 tile which gets a deliberate crop
    'gallery/01.jpg':         (9,  3 / 2,  0.62, 1300),
    'gallery/02.jpg':         (0,  None,   0.50, 1200),
    'gallery/03.jpg':         (1,  None,   0.50, 1200),
    'gallery/04.jpg':         (2,  None,   0.50, 1200),   # landscape -> wide tile
    'gallery/05.jpg':         (5,  None,   0.50, 1200),
    'gallery/06.jpg':         (4,  None,   0.50, 1200),
    'gallery/07.jpg':         (6,  None,   0.50, 1200),
    'gallery/08.jpg':         (7,  None,   0.50, 1200),
    'gallery/09.jpg':         (8,  None,   0.50, 1200),   # landscape -> wide tile
    'gallery/10.jpg':         (10, None,   0.50, 1200),
    'gallery/11.jpg':         (11, None,   0.50, 1200),
    'gallery/12.jpg':         (3,  None,   0.50, 1200),
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
