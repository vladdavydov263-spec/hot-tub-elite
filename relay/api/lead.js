/**
 * Hot Tub Elite — lead relay for Telegram.
 *
 * A Vercel Edge Function. The landing page POSTs a JSON lead here; this forwards
 * it to Telegram via sendMessage. It exists for one reason: the bot token must
 * never reach the browser. A token shipped in front-end JS can be read by anyone
 * who opens devtools, and once it is in a public repo GitHub reports it to
 * Telegram and the token is revoked.
 *
 * Environment variables (Vercel project settings):
 *   TELEGRAM_BOT_TOKEN  required, secret — from @BotFather
 *   TELEGRAM_CHAT_ID    optional — defaults to the group below
 *   ALLOWED_ORIGIN      optional — defaults to the GitHub Pages origin
 *
 * Only the token has to be set by hand; the other two have working defaults so
 * there is exactly one value that needs care.
 */

export const config = { runtime: 'edge' };

// Bot: @loghottube_bot. A chat id is inert without the token, so it is not a secret.
const DEFAULT_CHAT_ID = '-1003956851336';

// Several origins, not one: during a domain move both addresses serve the site, and
// a relay that knows only the new one silently rejects every lead from the old.
// ALLOWED_ORIGIN may override this with a comma-separated list.
const DEFAULT_ORIGINS = [
  'https://hottubelite.pl',
  'https://www.hottubelite.pl',
  'https://vladdavydov263-spec.github.io',
];

const FIELD_LIMITS = { name: 80, phone: 32, email: 120, message: 800, model: 60, page: 300 };

function corsHeaders(origin, allowed) {
  return {
    'Access-Control-Allow-Origin': allowed.includes(origin) ? origin : allowed[0],
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '86400',
    Vary: 'Origin',
  };
}

// Strip control characters so a lead cannot forge extra lines in the Telegram message.
function clean(value, limit) {
  if (typeof value !== 'string') return '';
  return value.replace(/[\u0000-\u001f\u007f]/g, ' ').trim().slice(0, limit);
}

function escapeHtml(value) {
  return value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function json(body, status, cors) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...cors, 'Content-Type': 'application/json' },
  });
}

export default async function handler(request) {
  const token = process.env.TELEGRAM_BOT_TOKEN;
  const chatId = process.env.TELEGRAM_CHAT_ID || DEFAULT_CHAT_ID;
  const allowedOrigins = (process.env.ALLOWED_ORIGIN || '')
    .split(',').map((o) => o.trim()).filter(Boolean);
  const allowed = allowedOrigins.length ? allowedOrigins : DEFAULT_ORIGINS;

  const origin = request.headers.get('Origin') || '';
  const cors = corsHeaders(origin, allowed);

  if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors });
  if (request.method !== 'POST') return json({ ok: false, error: 'method_not_allowed' }, 405, cors);

  if (!token) {
    console.error('TELEGRAM_BOT_TOKEN is not set');
    return json({ ok: false, error: 'not_configured' }, 500, cors);
  }

  // Reject calls from other sites reusing this endpoint.
  if (origin && !allowed.includes(origin)) {
    return json({ ok: false, error: 'forbidden_origin' }, 403, cors);
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return json({ ok: false, error: 'bad_json' }, 400, cors);
  }

  // Honeypot: real users never fill this field, bots do. Answer ok so they stop retrying.
  if (clean(body.company, 100)) return json({ ok: true }, 200, cors);

  const lead = {
    name: clean(body.name, FIELD_LIMITS.name),
    phone: clean(body.phone, FIELD_LIMITS.phone),
    email: clean(body.email, FIELD_LIMITS.email),
    message: clean(body.message, FIELD_LIMITS.message),
    model: clean(body.model, FIELD_LIMITS.model),
    page: clean(body.page, FIELD_LIMITS.page),
  };

  if (!lead.name || !lead.phone) {
    return json({ ok: false, error: 'missing_fields' }, 422, cors);
  }

  const lines = [
    '\u{1F6C1} <b>Nowe zapytanie — Hot Tub Elite</b>',
    '',
    `<b>Imię:</b> ${escapeHtml(lead.name)}`,
    `<b>Telefon:</b> ${escapeHtml(lead.phone)}`,
  ];
  if (lead.email) lines.push(`<b>E-mail:</b> ${escapeHtml(lead.email)}`);
  if (lead.model) lines.push(`<b>Model:</b> ${escapeHtml(lead.model)}`);
  if (lead.message) lines.push('', `<b>Wiadomość:</b> ${escapeHtml(lead.message)}`);
  lines.push('', `<i>${escapeHtml(lead.page || 'strona główna')}</i>`);
  lines.push(`<i>${new Date().toLocaleString('pl-PL', { timeZone: 'Europe/Warsaw' })}</i>`);

  const telegram = await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      chat_id: chatId,
      text: lines.join('\n'),
      parse_mode: 'HTML',
      disable_web_page_preview: true,
    }),
  });

  if (!telegram.ok) {
    // Never log the token — the URL contains it, so log only the status and body.
    console.error('telegram sendMessage failed', telegram.status, await telegram.text());
    return json({ ok: false, error: 'telegram_failed' }, 502, cors);
  }

  return json({ ok: true }, 200, cors);
}
