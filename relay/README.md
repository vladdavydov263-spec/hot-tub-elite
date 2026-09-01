# Lead relay

One Vercel Edge Function, `api/lead.js`. The landing page POSTs a lead here and this
forwards it to the Telegram group. It exists so the bot token stays server-side —
a token in front-end JS is readable by anyone with devtools, and a token committed to
a public repo gets revoked by Telegram automatically.

## Deploy

This folder is its own Vercel project. Set **Root Directory** to `relay` so Vercel
builds only this, not the static site (which is served by GitHub Pages).

```bash
cd relay
npx vercel login
npx vercel link
npx vercel env add TELEGRAM_BOT_TOKEN production
npx vercel --prod
```

`env add` prompts for the value and stores it in Vercel. It never enters this repo.

The endpoint is then `https://<project>.vercel.app/api/lead`. Put that URL into
`CONFIG.leadEndpoint` in `../index.html`.

## Environment

| Variable | Required | Default |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | yes, secret | — |
| `TELEGRAM_CHAT_ID` | no | `-1003956851336` |
| `ALLOWED_ORIGIN` | no | the GitHub Pages origin |

Only the token needs setting. The other two have working defaults baked into the
function, so there is exactly one value that has to be handled carefully.

`ALLOWED_ORIGIN` must track the site's domain — the function rejects submissions from
any other origin. `python3 ../set-domain.py <domain>` updates the default in the source;
if you override it in Vercel's settings instead, update it there too.

## Responses

| Status | Body | Meaning |
|---|---|---|
| 200 | `{"ok":true}` | Delivered (also returned for honeypot hits, so bots stop retrying) |
| 400 | `bad_json` | Body was not JSON |
| 403 | `forbidden_origin` | Called from an origin other than the site |
| 405 | `method_not_allowed` | Not a POST |
| 422 | `missing_fields` | Name or phone missing |
| 500 | `not_configured` | `TELEGRAM_BOT_TOKEN` is not set |
| 502 | `telegram_failed` | Telegram rejected it — usually the bot is not in the group, or was restricted |
