/**
 * Hot Tub Elite — lead relay for Telegram.
 *
 * Deployed as a Cloudflare Worker so the bot token never reaches the browser.
 * The landing page POSTs a JSON lead here; this worker formats it and forwards
 * it to Telegram via sendMessage.
 *
 * Required secrets (set with `wrangler secret put <NAME>`):
 *   TELEGRAM_BOT_TOKEN — token from @BotFather
 *   TELEGRAM_CHAT_ID   — target chat / group / channel id
 *
 * Optional vars (wrangler.toml [vars]):
 *   ALLOWED_ORIGIN     — exact origin allowed to call this worker
 */

const FIELD_LIMITS = { name: 80, phone: 32, email: 120, message: 800, model: 60, page: 300 };

function corsHeaders(env, request) {
  const allowed = env.ALLOWED_ORIGIN || '*';
  const origin = request.headers.get('Origin') || '';
  const value = allowed === '*' ? '*' : (origin === allowed ? origin : allowed);
  return {
    'Access-Control-Allow-Origin': value,
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '86400',
    'Vary': 'Origin',
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

export default {
  async fetch(request, env) {
    const cors = corsHeaders(env, request);

    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: cors });
    }
    if (request.method !== 'POST') {
      return new Response('Method Not Allowed', { status: 405, headers: cors });
    }

    // Reject calls from other origins when ALLOWED_ORIGIN is configured.
    if (env.ALLOWED_ORIGIN) {
      const origin = request.headers.get('Origin');
      if (origin && origin !== env.ALLOWED_ORIGIN) {
        return new Response(JSON.stringify({ ok: false, error: 'forbidden_origin' }), {
          status: 403, headers: { ...cors, 'Content-Type': 'application/json' },
        });
      }
    }

    let body;
    try {
      body = await request.json();
    } catch {
      return new Response(JSON.stringify({ ok: false, error: 'bad_json' }), {
        status: 400, headers: { ...cors, 'Content-Type': 'application/json' },
      });
    }

    // Honeypot: real users never fill this field, bots do.
    if (clean(body.company, 100)) {
      return new Response(JSON.stringify({ ok: true }), {
        status: 200, headers: { ...cors, 'Content-Type': 'application/json' },
      });
    }

    const lead = {
      name: clean(body.name, FIELD_LIMITS.name),
      phone: clean(body.phone, FIELD_LIMITS.phone),
      email: clean(body.email, FIELD_LIMITS.email),
      message: clean(body.message, FIELD_LIMITS.message),
      model: clean(body.model, FIELD_LIMITS.model),
      page: clean(body.page, FIELD_LIMITS.page),
    };

    if (!lead.name || !lead.phone) {
      return new Response(JSON.stringify({ ok: false, error: 'missing_fields' }), {
        status: 422, headers: { ...cors, 'Content-Type': 'application/json' },
      });
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

    const telegram = await fetch(
      `https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chat_id: env.TELEGRAM_CHAT_ID,
          text: lines.join('\n'),
          parse_mode: 'HTML',
          disable_web_page_preview: true,
        }),
      }
    );

    if (!telegram.ok) {
      const detail = await telegram.text();
      console.error('telegram sendMessage failed', telegram.status, detail);
      return new Response(JSON.stringify({ ok: false, error: 'telegram_failed' }), {
        status: 502, headers: { ...cors, 'Content-Type': 'application/json' },
      });
    }

    return new Response(JSON.stringify({ ok: true }), {
      status: 200, headers: { ...cors, 'Content-Type': 'application/json' },
    });
  },
};
