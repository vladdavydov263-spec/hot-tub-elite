#!/usr/bin/env python3
"""
Point the site at a custom domain.

The site URL is baked into eight places — canonical link, Open Graph tags,
three JSON-LD blocks, robots.txt, sitemap.xml — plus the worker's
ALLOWED_ORIGIN, which rejects lead submissions from any other origin. Miss that
last one and the contact form starts failing with a CORS error the moment the
domain changes, which is the kind of breakage nobody notices until leads stop
arriving. So: one command updates all of them together.

    python3 set-domain.py hottubelite.pl
    python3 set-domain.py www.hottubelite.pl
    python3 set-domain.py --dry-run hottubelite.pl

Writing the CNAME file is only half the job — the DNS records still have to be
added at the registrar. Run with no arguments to print those records.
"""

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).parent

GITHUB_PAGES_IPS = [
    '185.199.108.153',
    '185.199.109.153',
    '185.199.110.153',
    '185.199.111.153',
]
GITHUB_USER = 'vladdavydov263-spec'

# Files that carry the site URL, and the worker config that carries the origin.
URL_FILES = ['index.html', 'robots.txt', 'sitemap.xml']
ORIGIN_FILES = ['worker/wrangler.toml']


def current_base() -> str:
    """Read the site URL currently baked into the canonical link."""
    html = (ROOT / 'index.html').read_text(encoding='utf-8')
    m = re.search(r'<link rel="canonical" href="([^"]+)"', html)
    if not m:
        sys.exit('Could not find the canonical link in index.html.')
    return m.group(1)


def print_dns(domain: str) -> None:
    apex = not domain.startswith('www.')
    print(f'\nDNS records to add at the registrar for {domain}:\n')
    if apex:
        print('  Four A records on the root (@):')
        for ip in GITHUB_PAGES_IPS:
            print(f'    @    A      {ip}')
        print(f'\n  And so www works too:')
        print(f'    www  CNAME  {GITHUB_USER}.github.io.')
    else:
        bare = domain[4:]
        print(f'    www  CNAME  {GITHUB_USER}.github.io.')
        print(f'\n  Optional, so the bare domain redirects to www:')
        for ip in GITHUB_PAGES_IPS:
            print(f'    @    A      {ip}    ({bare})')
    print('\nThen in the repo: Settings -> Pages -> Custom domain -> enter the domain,')
    print('wait for the DNS check to pass, and tick "Enforce HTTPS".')
    print('The certificate takes ~15 minutes and can take an hour. Until it is issued')
    print('the browser will warn about the connection — that is expected, not a fault.\n')


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('domain', nargs='?', help='e.g. hottubelite.pl or www.hottubelite.pl')
    ap.add_argument('--dry-run', action='store_true', help='show the changes without writing')
    args = ap.parse_args()

    if not args.domain:
        print_dns('example.pl')
        sys.exit('Pass the domain to apply it, e.g.  python3 set-domain.py hottubelite.pl')

    domain = args.domain.strip().lower().removeprefix('https://').removeprefix('http://').rstrip('/')
    if not re.fullmatch(r'[a-z0-9-]+(\.[a-z0-9-]+)+', domain):
        sys.exit(f'"{domain}" does not look like a domain name.')

    old_base = current_base()                       # e.g. https://user.github.io/hot-tub-elite/
    old_origin = re.match(r'(https?://[^/]+)', old_base).group(1)
    new_base = f'https://{domain}/'
    new_origin = f'https://{domain}'

    if old_base == new_base:
        print(f'Already pointing at {domain}. Nothing to change.')
        print_dns(domain)
        return

    print(f'{old_base}  ->  {new_base}\n')

    for name in URL_FILES + ORIGIN_FILES:
        path = ROOT / name
        text = path.read_text(encoding='utf-8')
        # Longest match first: the base URL contains the origin.
        updated = text.replace(old_base, new_base).replace(old_origin, new_origin)
        hits = len(text.split(old_origin)) - 1
        if updated != text and not args.dry_run:
            path.write_text(updated, encoding='utf-8')
        print(f'  {name:24s} {hits} occurrence(s){"" if not args.dry_run else "  (dry run)"}')

    if not args.dry_run:
        (ROOT / 'CNAME').write_text(domain + '\n', encoding='utf-8')
        print(f'  {"CNAME":24s} written: {domain}')
        print('\nCommit and push, then add the DNS records below.')
    else:
        print(f'  {"CNAME":24s} would contain: {domain}  (dry run)')

    print_dns(domain)


if __name__ == '__main__':
    main()
