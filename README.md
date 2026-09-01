# Hot Tub Elite — landing page

Static landing page for a Polish garden-jacuzzi manufacturer. Hosted on GitHub Pages.
Lead forms are relayed to Telegram through a Vercel Edge Function so the bot token is
never exposed in the browser.

```
index.html                  the page
polityka-prywatnosci.html   RODO/GDPR privacy policy
favicon.svg  robots.txt  sitemap.xml  .nojekyll
images/                     photos — see images/README.md
relay/                      Vercel Edge Function that forwards leads to Telegram
```

---

## 1. Telegram bot

Already set up: bot **@loghottube_bot**, posting into group **-1003956851336**.
The chat id is a default inside `relay/api/lead.js` — it is useless without the token,
so there is no reason to hide it.

> **The bot token is a password.** It must never appear in `index.html`, in this repo,
> or in any commit. If it ever lands in a public repo, GitHub reports it to Telegram
> and the token is revoked automatically. Step 2 sets it directly in Vercel, so it
> never touches the repo. If it does leak, regenerate it with `/revoke` in @BotFather.

Check the bot is actually in the group and allowed to post there — a bot that was
added but then restricted will make `sendMessage` fail with 403, and the relay will
answer the form with `telegram_failed`.

## 2. Deploy the relay

`relay/` is its own Vercel project. Set **Root Directory** to `relay` in the project
settings so Vercel builds only the function — the site itself is served by GitHub Pages.

```bash
cd relay
npx vercel login
npx vercel link
npx vercel env add TELEGRAM_BOT_TOKEN production
npx vercel --prod
```

`env add` prompts for the token and stores it in Vercel; it never enters this repo.
`--prod` prints the deployment URL, and the endpoint is that URL plus `/api/lead`.

> Vercel's Hobby plan is for non-commercial projects. This site sells hot tubs, so
> check whether the account's plan covers it — a suspended relay fails silently and
> the form starts dropping leads.

## 3. Point the page at the relay

In `index.html`, find the `CONFIG` block near the bottom and set:

```js
leadEndpoint: 'https://<project>.vercel.app/api/lead',
```

Until this is filled in, the form falls back to opening WhatsApp with a prefilled
message — leads still reach you, they just take one extra tap.

## 4. Add the photos

Drop new photos into `images/inbox/<group>/` and run:

```bash
python3 place-photos.py && python3 build-preview.py
```

`place-photos.py` holds the source-to-slot map. Each entry carries a target aspect
ratio and a vertical focal point, because the source shots are phone photos in mixed
orientations and a plain centred crop cuts the tub in half. Edit the `PLAN` table to
re-assign or re-frame a photo, then re-run.

`build-preview.py` regenerates `preview.html`, the single self-contained file published
as a shareable Artifact: photos inlined as data: URIs at a smaller size, the privacy
policy folded in as a section, and all non-ASCII escaped so Polish diacritics survive
regardless of the charset the host serves.

See `images/README.md` for the slot names and sizes. Any missing photo renders as a
dark placeholder tile showing the expected filename, so the page never looks broken
mid-migration.

## 5. Publish on GitHub Pages

```bash
git init
git add .
git commit -m "feat: hot tub elite landing page"
git branch -M main
git remote add origin git@github.com:<user>/hot-tub-elite.git
git push -u origin main
```

Then in the repo: **Settings → Pages → Source: Deploy from a branch → `main` / `root`.**

## 6. Replace the CHANGE-ME placeholders

Search the repo for `CHANGE-ME` and swap in the real domain. It appears in:

- `index.html` — canonical URL, Open Graph tags, JSON-LD structured data
- `robots.txt`, `sitemap.xml`
- `relay/api/lead.js` — `DEFAULT_ORIGIN`

```bash
grep -rn "CHANGE-ME" .
```

## 7. Custom domain

The site currently answers at `https://vladdavydov263-spec.github.io/hot-tub-elite/`.
To move it to a real domain, run one command — it rewrites the URL everywhere it is
baked in and writes the `CNAME` file:

```bash
python3 set-domain.py hottubelite.pl
```

Add `--dry-run` first to see what changes. Then commit, push, and add the DNS records
the script prints (it prints them on its own with no arguments too).

The URL lives in eight places — canonical link, Open Graph tags, three JSON-LD blocks,
`robots.txt`, `sitemap.xml` — plus `DEFAULT_ORIGIN` in `relay/api/lead.js`. That last
one is the trap: the relay rejects lead submissions from any origin it does not
recognise, so changing the domain by hand and forgetting the relay leaves a contact
form that fails with a CORS error and drops every lead silently. After changing the
domain, redeploy the relay:

```bash
cd relay && npx vercel --prod
```

Finally, in the repo: **Settings → Pages → Custom domain**, enter the domain, wait for
the DNS check to pass, then tick **Enforce HTTPS**. The certificate takes about
15 minutes and can take an hour; until it is issued the browser warns about the
connection. That is expected — nothing is broken, it just has not been issued yet.

The old `github.io` address keeps working and redirects to the new domain, so links
already sent out do not break.

## 8. Analytics (optional)

Fill `ga4Id` and/or `metaPixelId` in the `CONFIG` block. Both stay dormant until the
visitor accepts the cookie banner — required under GDPR. Leave them empty and the
banner never appears.

---

## Local preview

```bash
python3 -m http.server 8000
```

Then open <http://localhost:8000>.

## Things to confirm with the client

- **Warranty period.** The stats bar says 24 months and the original FAQ said 12.
  Both now say 24 — change the FAQ answer and the stats tile together if that is wrong.
- **Company details in the privacy policy.** The `[DANE FIRMY]` placeholders must be
  filled with the real registered name, address and NIP before launch.
- **Review authenticity.** The three testimonials are carried over from the original page.
- **Gallery photos — decided, do not re-raise.** Some supplied shots are catalogue renders
  rather than the client's own installations, while the gallery heading claims
  "zdjęcia zrealizowanych wanien SPA u naszych klientów". This was flagged and the owner
  chose to publish all of them as-is. Place every supplied photo without filtering.
- **Prices.** Model cards say "Zapytaj o cenę". Add real prices if the client wants them public.
- **Wood-stove price and currency.** The optional external wood stove is published as
  **+20 000 zł** (PLN) in three places: the `#piec` section, the tag on all three model
  cards, and the JSON-LD `Offer`. Confirm both the number and the currency before launch —
  a wrong public price is the expensive kind of typo. Search for `20 000 zł` and `"20000"`.
- **Wood stove availability.** Currently presented as an option for every model. If it only
  fits some of them, the tag must come off the cards it does not apply to.
