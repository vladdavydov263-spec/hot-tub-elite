#!/usr/bin/env python3
"""
Build preview.html — a single self-contained file for publishing as an Artifact.

The artifact host supplies <!doctype>/<head>/<body>, so this strips our own
skeleton, inlines every photo we have as a data: URI, folds the privacy policy
into an in-page section (there is no second file to link to), and escapes all
non-ASCII so the page renders correctly no matter what charset it is served as.

Re-run this after adding photos or editing index.html:

    python3 build-preview.py
"""

import base64
import io
import pathlib
import re

from PIL import Image

ROOT = pathlib.Path(__file__).parent

# Every photo is inlined as base64, which costs ~34% on top of the file size and
# all of it lands in one page load. The published site serves the full-size
# files; the shareable preview re-encodes smaller so it stays quick to open.
PREVIEW_MAX_EDGE = 900
PREVIEW_QUALITY = 76


def inline_jpeg(path: pathlib.Path) -> str:
    im = Image.open(path)
    im.thumbnail((PREVIEW_MAX_EDGE, PREVIEW_MAX_EDGE), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, 'JPEG', quality=PREVIEW_QUALITY, optimize=True, progressive=True)
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()


def escape_non_ascii_html(text: str) -> str:
    """Non-ASCII -> numeric HTML entities. Charset-independent."""
    return ''.join(c if ord(c) < 128 else f'&#{ord(c)};' for c in text)


def escape_non_ascii_js(text: str) -> str:
    """Non-ASCII -> \\uXXXX. Valid in both JS and JSON string literals."""
    return ''.join(c if ord(c) < 128 else f'\\u{ord(c):04x}' for c in text)


def escape_document(html: str) -> str:
    """Escape non-ASCII everywhere, using the right scheme per context.

    HTML entities are inert inside <script> and <style> (both are raw-text
    elements), so those blocks get JS-style escapes instead.
    """
    parts = re.split(r'(<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>)', html, flags=re.S)
    out = []
    for part in parts:
        if part.startswith('<script') or part.startswith('<style'):
            open_tag, rest = part.split('>', 1)
            out.append(open_tag + '>' + escape_non_ascii_js(rest))
        else:
            out.append(escape_non_ascii_html(part))
    return ''.join(out)


def main() -> None:
    src = (ROOT / 'index.html').read_text(encoding='utf-8')

    head = re.search(r'<head>(.*?)</head>', src, re.S).group(1)
    body = re.search(r'<body>(.*?)</body>', src, re.S).group(1)

    fonts = re.search(r'<link href="https://fonts\.googleapis[^>]*>', head).group(0)
    preconnects = '\n'.join(re.findall(r'<link rel="preconnect"[^>]*>', head))
    style = re.search(r'<style>.*?</style>', head, re.S).group(0)

    # The artifact carries its own name and icon; the URL-bound SEO tags and the
    # file-based favicon have no meaning here.
    out_head = f'<title>Hot Tub Elite</title>\n{preconnects}\n{fonts}\n{style}'

    # --- inline every photo that exists; the rest keep their placeholder tiles ---
    inlined = []
    for img in sorted(ROOT.joinpath('images').rglob('*.jpg')):
        if 'inbox' in img.parts:
            continue
        rel = img.relative_to(ROOT).as_posix()
        needle = f'src="{rel}"'
        if needle in body:
            body = body.replace(needle, f'src="{inline_jpeg(img)}"')
            inlined.append(rel)

    # --- the gallery is built in JS, so its photos need an explicit lookup table ---
    gallery_map = []
    for img in sorted(ROOT.joinpath('images', 'gallery').glob('*.jpg')):
        gallery_map.append(f'"{img.name}":"{inline_jpeg(img)}"')
        inlined.append(f'images/gallery/{img.name}')
    if gallery_map:
        body = ('<script>window.GALLERY_SRC={' + ','.join(gallery_map) + '};</script>\n') + body

    # --- privacy policy becomes a section instead of a second page ---
    pol = (ROOT / 'polityka-prywatnosci.html').read_text(encoding='utf-8')
    pol_body = re.search(r'<div class="wrap">(.*?)</div>\s*<script>', pol, re.S).group(1)
    pol_body = re.sub(r'<a class="back".*?</a>', '', pol_body, flags=re.S)
    pol_body = re.sub(r'<div class="todo">.*?</div>', '', pol_body, flags=re.S)  # internal note
    pol_body = re.sub(r'<footer>.*?</footer>', '', pol_body, flags=re.S)
    pol_body = pol_body.replace('<a href="index.html">Strona główna</a>', '')
    pol_body = pol_body.replace('id="updated"', 'id="pol-updated"').replace('id="year"', 'id="pol-year"')

    policy_section = (
        '\n<section class="block" id="polityka" style="background:var(--cream-2)">\n'
        '  <div class="container" style="max-width:820px">\n'
        f'    <div class="policy">{pol_body}</div>\n'
        '  </div>\n'
        '</section>\n'
    )

    body = re.sub(r'href="polityka-prywatnosci\.html"', 'href="#polityka"', body)
    body = body.replace('href="#polityka" target="_blank" rel="noopener"', 'href="#polityka"')
    body = body.replace('<footer>', policy_section + '\n<footer>', 1)

    extra_css = '''
<style>
.policy h1{font-size:clamp(1.8rem,4vw,2.6rem);font-weight:500;margin-bottom:8px}
.policy h2{font-size:1.3rem;font-weight:500;margin:32px 0 10px}
.policy p,.policy li{color:var(--espresso-soft);margin-bottom:11px;font-size:.96rem;line-height:1.7}
.policy ul{padding-left:22px}
.policy a{color:var(--amber-deep)}
.policy .updated{font-size:.85rem;padding-bottom:20px;border-bottom:1px solid var(--line);margin-bottom:8px}
.preview-bar{background:var(--espresso);color:var(--cream);font-size:.84rem;font-weight:700;
  padding:.7rem 24px;display:flex;align-items:center;justify-content:center;gap:14px;
  flex-wrap:wrap;text-align:center}
.preview-bar em{font-style:normal;color:rgba(248,248,249,.72);font-weight:500}
.preview-bar button{background:transparent;border:1px solid var(--line-dark);color:var(--cream);
  border-radius:100px;padding:.25rem .8rem;font:inherit;font-size:.78rem;cursor:pointer}
.preview-bar button:hover{background:rgba(248,248,249,.1)}
</style>
'''

    preview_bar = '''
<div class="preview-bar" id="previewBar">
  Podgląd roboczy
  <em>Zdjęcia i formularz kontaktowy są jeszcze podłączane.</em>
  <button type="button" id="hidePreviewBar">Ukryj</button>
</div>
'''

    tail_script = '''
<script>
  document.getElementById('hidePreviewBar')
    .addEventListener('click', () => document.getElementById('previewBar').remove());
  const polNow = new Date();
  const polYear = document.getElementById('pol-year');
  const polUpdated = document.getElementById('pol-updated');
  if (polYear) polYear.textContent = polNow.getFullYear();
  if (polUpdated) polUpdated.textContent =
    polNow.toLocaleDateString('pl-PL', { year: 'numeric', month: 'long' });
</script>
'''

    doc = out_head + extra_css + preview_bar + body + tail_script
    doc = escape_document(doc)

    out = ROOT / 'preview.html'
    out.write_text(doc, encoding='ascii')

    print('inlined photos:', len(inlined))
    for rel in inlined:
        print('  ', rel)
    print(f'preview.html: {out.stat().st_size / 1024:.0f} KB')


if __name__ == '__main__':
    main()
