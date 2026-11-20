/* Cloudflare Worker: receives the website forms and talks to Brevo.
 *
 *   POST /lead   { name, phone, email, service, item, message, marketing_consent, source, website }
 *
 * What it does for every lead (same rules as mailer.py on the Python server):
 *   1. emails Anna Lee a note with the details (NOTIFY_EMAIL)
 *   2. with an email address: adds the contact to the list of what they asked for (the lecture, a workshop, a free tool: see ITEM_LISTS in wrangler.toml)
 *      and to the newsletter list (only with marketing consent)
 *   3. for the lecture "על קוצים": sends the confirmation email
 * The Brevo key lives only here, as a secret. Nothing is stored in the Worker.
 */
const SERVICES = ['therapy', 'breathwork', 'workshop', 'lecture', 'free', 'general'];
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const PHONE_RE = /^[0-9+\-\s()]{7,20}$/;
const OK_MESSAGE = 'התקבל. נחזור אלייך בתוך 48 שעות.';
const LECTURE_TITLE = 'על קוצים: למה הגוף שלך כל הזמן בכוננות ואיך מפסיקים לפחד מהחרדה';
const FOOTER = 'קיבלת את המייל הזה כי נרשמת להרצאה באתר של אנה לי מילשטיין. אם זו טעות, אפשר פשוט להשיב למייל.';
const DAYS = ['יום ראשון', 'יום שני', 'יום שלישי', 'יום רביעי', 'יום חמישי', 'יום שישי', 'שבת'];

const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const clean = (v, max) => (typeof v === 'string' ? v.replace(/[\u0000-\u001f]/g, ' ').trim().slice(0, max) : '');

function cors(env, req) {
  const allowed = (env.ALLOWED_ORIGINS || '').split(',').map((s) => s.trim()).filter(Boolean);
  const origin = req.headers.get('origin') || '';
  return {
    'access-control-allow-origin': allowed.includes(origin) ? origin : allowed[0] || '',
    'access-control-allow-methods': 'POST, OPTIONS',
    'access-control-allow-headers': 'content-type',
    'access-control-max-age': '86400',
    vary: 'origin',
  };
}
const reply = (env, req, status, data) =>
  new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store', ...cors(env, req) } });

async function brevo(env, path, payload) {
  const r = await fetch('https://api.brevo.com/v3' + path, {
    method: 'POST',
    headers: { 'api-key': env.BREVO_API_KEY, 'content-type': 'application/json', accept: 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!r.ok) throw new Error(`Brevo ${path} ${r.status}: ${(await r.text()).slice(0, 200)}`);
}

function page(body, footer) {
  return `<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><style>
body{margin:0;background:#FBF6EF;font-family:Arial,Helvetica,sans-serif;color:#4C392F}
.card{max-width:560px;margin:0 auto;padding:36px 28px;font-size:17px;line-height:1.7;text-align:right}
.btn{display:inline-block;background:#94455A;color:#FFF8F3!important;text-decoration:none;border-radius:999px;padding:12px 28px;font-weight:bold}
.foot{font-size:13px;color:#6E5648;border-top:1px solid #EAD9CF;padding-top:16px;margin-top:28px}
</style></head><body><div class="card">${body}${footer ? `<p class="foot">${esc(FOOTER)}</p>` : ''}</div></body></html>`;
}

async function sendMail(env, to, toName, subject, body, footer) {
  await brevo(env, '/smtp/email', {
    sender: { email: env.BREVO_SENDER_EMAIL, name: env.BREVO_SENDER_NAME || 'אנה לי מילשטיין' },
    to: [{ email: to, name: toName || to }],
    subject,
    htmlContent: page(body, footer),
  });
}

// The list of what the form was about: the first entry of ITEM_LISTS ([["text in the form's topic", list number], ...]) that fits.
function itemList(env, topic) {
  let pairs = [];
  try { pairs = JSON.parse(env.ITEM_LISTS || '[]'); } catch (e) { console.error('[lead] ITEM_LISTS is not valid JSON'); }
  for (const [needle, id] of pairs) if (topic.includes(needle) && Number.isInteger(+id)) return +id;
  return 0;
}

// The list of a form that has no topic of its own: by the kind of service (the clinic, breathwork), and the contact page's general list.
function serviceList(env, lead) {
  let by = {};
  try { by = JSON.parse(env.SERVICE_LISTS || '{}'); } catch (e) { console.error('[lead] SERVICE_LISTS is not valid JSON'); }
  if (Number.isInteger(+by[lead.service]) && +by[lead.service] > 0) return +by[lead.service];
  if (/contact/.test(lead.source || '') && Number.isInteger(+env.CONTACT_LIST) && +env.CONTACT_LIST > 0) return +env.CONTACT_LIST;
  return 0;
}

function lectureWhen(env) {
  const [y, m, d] = String(env.LECTURE_DATE || '').split('-').map(Number);
  if (!y) return { when: '', time: env.LECTURE_TIME || '' };
  const dt = new Date(Date.UTC(y, m - 1, d));
  return { when: `${DAYS[dt.getUTCDay()]}, ${String(d).padStart(2, '0')}.${String(m).padStart(2, '0')}`, time: env.LECTURE_TIME || '' };
}

async function followUp(env, lead) {
  const jobs = [];
  const topic = lead.item || 'פנייה כללית';
  const isLecture = topic.includes('על קוצים');

  if (env.NOTIFY_EMAIL) {
    const msg = lead.message ? `<p><strong>הודעה:</strong><br>${esc(lead.message)}</p>` : '';
    jobs.push(sendMail(env, env.NOTIFY_EMAIL, env.BREVO_SENDER_NAME, `פנייה חדשה מהאתר: ${lead.name} (${topic})`,
      `<p><strong>${esc(lead.name)}</strong> השאירה פרטים באתר.</p>
<p><strong>נושא:</strong> ${esc(topic)}<br><strong>מייל:</strong> ${esc(lead.email || '-')}<br><strong>טלפון:</strong> ${esc(lead.phone || '-')}<br><strong>הסכמה לדיוור:</strong> ${lead.marketing ? 'כן' : 'לא'}</p>${msg}`, false));
  }
  if (lead.email) {
    const lists = [];
    if (isLecture && env.BREVO_LIST_REGISTRANTS) lists.push(+env.BREVO_LIST_REGISTRANTS);
    const itemId = itemList(env, topic) || serviceList(env, lead);
    if (itemId && !lists.includes(itemId)) lists.push(itemId);
    if (lead.marketing && env.BREVO_LIST_ID) lists.push(+env.BREVO_LIST_ID);
    if (lists.length) jobs.push(brevo(env, '/contacts', { email: lead.email, attributes: { FIRSTNAME: lead.name }, listIds: lists, updateEnabled: true }));
    // The lecture confirmation email is now sent by the Brevo automation (trigger: contact added to list #4),
    // so it is not sent from here any more. Notification to Anna and the list sign-ups above are unchanged.
  }
  // Every job is attempted; a failure is logged (Workers logs) and never blocks the visitor.
  for (const r of await Promise.allSettled(jobs)) if (r.status === 'rejected') console.error('[lead]', r.reason && r.reason.message);
}

export default {
  async fetch(req, env, ctx) {
    const url = new URL(req.url);
    if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors(env, req) });
    if (url.pathname !== '/lead' || req.method !== 'POST') return reply(env, req, 404, { error: 'לא נמצא' });

    const allowed = (env.ALLOWED_ORIGINS || '').split(',').map((s) => s.trim()).filter(Boolean);
    const origin = req.headers.get('origin') || '';
    if (allowed.length && !allowed.includes(origin)) return reply(env, req, 403, { error: 'לא מורשה' });

    const raw = await req.text();
    if (raw.length > 10000) return reply(env, req, 413, { error: 'הבקשה גדולה מדי.' });
    let data;
    try { data = JSON.parse(raw || '{}'); } catch { return reply(env, req, 400, { error: 'הבקשה אינה תקינה.' }); }

    if (clean(data.website, 200)) return reply(env, req, 200, { message: OK_MESSAGE });   // honeypot: bots fill it

    const lead = {
      name: clean(data.name, 100), phone: clean(data.phone, 30), email: clean(data.email, 120),
      service: clean(data.service, 30) || 'general', item: clean(data.item, 200), message: clean(data.message, 2000),
      marketing: data.marketing_consent === true, source: clean(data.source, 200),
    };
    if (lead.name.length < 2) return reply(env, req, 400, { error: 'נא להזין שם.' });
    if (!lead.phone && !lead.email) return reply(env, req, 400, { error: 'נא להזין טלפון או מייל.' });
    if (lead.phone && !PHONE_RE.test(lead.phone)) return reply(env, req, 400, { error: 'מספר הטלפון אינו נראה תקין.' });
    if (lead.email && !EMAIL_RE.test(lead.email)) return reply(env, req, 400, { error: 'כתובת המייל אינה נראית תקינה.' });
    if (!SERVICES.includes(lead.service)) return reply(env, req, 400, { error: 'סוג השירות אינו תקין.' });
    if (!env.BREVO_API_KEY || !env.BREVO_SENDER_EMAIL) return reply(env, req, 503, { error: 'השירות עדיין לא מוגדר.' });

    ctx.waitUntil(followUp(env, lead));   // the visitor never waits for Brevo
    return reply(env, req, 200, { message: OK_MESSAGE });
  },
};
