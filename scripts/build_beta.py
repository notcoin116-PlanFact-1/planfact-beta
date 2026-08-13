from pathlib import Path
import subprocess
import sys

p = Path(sys.argv[1] if len(sys.argv) > 1 else "site/index.html")
s = p.read_text(encoding="utf-8")

direct = "https://vjglqivddspcolrzxmxt.supabase.co/functions/v1/planfact-beta-api"
gateway = "https://vjglqivddspcolrzxmxt.supabase.co/functions/v1/planfact-beta-gateway"
s = s.replace(direct, gateway)

# Repair known inline handlers produced by the temporary Supabase HTML generator.
s = s.replace("onclick=\"nav(''+x[0]+'')\"", "onclick=\"nav(&quot;'+x[0]+'&quot;)\"")
s = s.replace("onclick=\"nav('plans')\"", "onclick=\"nav(&quot;plans&quot;)\"")

def replace_block(text, start_marker, end_marker, replacement):
    a = text.find(start_marker)
    b = text.find(end_marker, a)
    if a < 0 or b <= a:
        raise SystemExit(f"Beta patch marker missing: {start_marker} -> {end_marker}")
    return text[:a] + replacement + text[b:]

helpers = "\nfunction pairKey(v){return String(v||'').toUpperCase().replace(/[^A-Z0-9]/g,'')}\nfunction tradeTs(t){var v=String((t&&t.tradeDate)||(t&&t.closedAt)||(t&&t.createdAt)||'');var n=Date.parse(v);return Number.isFinite(n)?n:0}\nfunction fmtDate(v){var x=String(v||'').trim(),m=x.match(/^(\\d{4})-(\\d{2})-(\\d{2})T(\\d{2}):(\\d{2})/);if(m)return m[3]+'.'+m[2]+'.'+m[1]+' '+m[4]+':'+m[5];return x.replace('T',' ').replace(/\\.\\d{3}Z?$/,'')}\nfunction toggleSort(){var b=q('#fsort');if(!b)return;var old=b.getAttribute('data-dir')||'desc',next=old==='desc'?'asc':'desc';b.setAttribute('data-dir',next);b.textContent=next==='desc'?'↓ Сначала новые':'↑ Сначала старые';filterTrades()}\n"
anchor = "function planLinkedSet"
pos = s.find(anchor)
if pos < 0:
    raise SystemExit("Beta helper anchor missing")
s = s[:pos] + helpers + s[pos:]

s = replace_block(s, "function trades()", "function filterTrades()", 'function trades(){q(\'#view\').innerHTML=\'<div class="between"><h1>Сделки</h1><button class="btn small" onclick="tradeModal()">+ Сделка</button></div><div class="filters"><input id="fsym" placeholder="Пара" oninput="filterTrades()"><select id="fdir" onchange="filterTrades()"><option value="">Long / Short</option><option>Long</option><option>Short</option></select><select id="fstatus" onchange="filterTrades()"><option value="">Статус</option><option value="open">Открытые</option><option value="closed">Закрытые</option></select><select id="fsource" onchange="filterTrades()"><option value="">Источник</option><option value="manual">Вручную</option><option value="screenshot">Скриншот</option><option value="bingx">BingX</option></select><select id="fpnl" onchange="filterTrades()"><option value="">P&L</option><option value="plus">Прибыльные</option><option value="minus">Убыточные</option></select><select id="fplan" onchange="filterTrades()"><option value="">План</option><option value="yes">С планом</option><option value="no">Без плана</option></select><input id="fstrat" placeholder="Стратегия" oninput="filterTrades()"><button id="fsort" class="btn secondary" data-dir="desc" onclick="toggleSort()">↓ Сначала новые</button></div><div id="tradeList"></div>\';filterTrades()}\n')
s = replace_block(s, "function filterTrades()", "function plans()", 'function filterTrades(){var a=(state.trades||[]).slice(),sym=(q(\'#fsym\')||{}).value||\'\',d=(q(\'#fdir\')||{}).value||\'\',st=(q(\'#fstatus\')||{}).value||\'\',src=(q(\'#fsource\')||{}).value||\'\',pp=(q(\'#fpnl\')||{}).value||\'\',pl=(q(\'#fplan\')||{}).value||\'\',str=(q(\'#fstrat\')||{}).value||\'\',sort=(q(\'#fsort\')||{}).getAttribute?q(\'#fsort\').getAttribute(\'data-dir\')||\'desc\':\'desc\',links=planLinkedSet();if(sym){var sk=pairKey(sym);a=a.filter(function(t){return pairKey(t.pair).indexOf(sk)>=0})}if(d)a=a.filter(function(t){return String(t.direction||\'\').toLowerCase()===d.toLowerCase()});if(st)a=a.filter(function(t){return st===\'closed\'?closed(t):!closed(t)});if(src)a=a.filter(function(t){return String(t.source||\'manual\').toLowerCase()===src.toLowerCase()});if(pp)a=a.filter(function(t){return pp===\'plus\'?pnl(t)>0:pnl(t)<0});if(pl)a=a.filter(function(t){return pl===\'yes\'?!!links[t.id]:!links[t.id]});if(str)a=a.filter(function(t){return String(t.strategy||\'\').toLowerCase().indexOf(str.toLowerCase())>=0});a.sort(function(left,right){return sort===\'asc\'?tradeTs(left)-tradeTs(right):tradeTs(right)-tradeTs(left)});q(\'#tradeList\').innerHTML=a.length?a.map(function(t){return\'<article class="trade"><div class="between"><b>\'+esc(t.pair)+\' · \'+esc(t.direction)+\'</b><b class="\'+(pnl(t)>=0?\'green\':\'red\')+\'">\'+(closed(t)?pnl(t).toFixed(2)+\' USDT\':\'OPEN\')+\'</b></div><div class="muted">\'+esc(fmtDate(t.tradeDate||t.createdAt||\'\'))+\' · \'+esc(t.source||\'manual\')+\'</div><div class="row"><span class="pill">Entry \'+esc(t.entry||\'\')+\'</span>\'+(t.exit?\'<span class="pill">Exit \'+esc(t.exit)+\'</span>\':\'\')+(links[t.id]?\'<span class="pill">Есть план</span>\':\'\')+\'</div><button class="btn small danger" onclick="removeTrade(&quot;\'+esc(t.id)+\'&quot;)">Удалить</button></article>\'}).join(\'\'):\'<div class="empty">Сделок по выбранным параметрам нет.</div>\'}\n')
s = replace_block(s, "function patterns()", "function profile()", 'function patterns(){var tr=(state.trades||[]).filter(closed),d=tr.filter(function(t){return t.followedPlan||t.emotion||t.impulse}),ready=tr.filter(function(t){return[\'Да\',\'Частично\',\'Нет\'].indexOf(String(t.followedPlan||\'\'))>=0&&String(t.emotion||\'\').trim()&&String(t.impulse||\'\').trim()}),broken=d.filter(function(t){return t.followedPlan===\'Нет\'||t.followedPlan===\'Частично\'}),need=Math.max(0,5-ready.length),ai=\'\';if(!state.access.isPro)ai=\'<p class="muted">Доступно в Beta Pro.</p>\';else if(ready.length<5)ai=\'<button class="btn secondary" disabled>AI-анализ пока недоступен</button><p class="muted">Для анализа нужно минимум 5 сделок, где заполнены «Соблюдение плана», «Эмоция» и «Импульс / причина». Сейчас готово: \'+ready.length+\'/5. Нужно ещё: \'+need+\'.</p>\';else ai=\'<button class="btn dark" onclick="runAI()">Запустить AI-анализ</button>\';q(\'#view\').innerHTML=\'<h1>Ошибки</h1><div class="grid"><div class="stat"><span class="muted">С данными</span><b>\'+d.length+\'</b></div><div class="stat"><span class="muted">Нарушен план</span><b>\'+broken.length+\'</b></div></div><div class="card"><h2>AI-анализ дисциплины</h2><p class="muted">Анализирует только повторяющиеся привычки и соблюдение плана, без торговых сигналов.</p>\'+ai+\'<div id="aiout"></div></div>\'}\n')
s = replace_block(s, "async function runAI()", "function supportModal()", 'async function runAI(){var out=q(\'#aiout\');out.innerHTML=\'<div class="aiout">Анализируем…</div>\';try{var b=await call(\'analyze_discipline\'),a=b.analysis||{},txt=(a.summary||\'\')+\'\\n\\n\'+(a.patterns||[]).map(function(p){return\'• \'+p.title+\'\\n\'+p.evidence+\'\\nДействие: \'+p.practicalAction}).join(\'\\n\\n\')+\'\\n\\nСледующий шаг: \'+(a.nextStep||\'\');out.innerHTML=\'<div class="aiout">\'+esc(txt)+\'</div>\'}catch(e){var code=e.code||e.message,text=code===\'not_enough_trades_for_analysis\'?\'Недостаточно заполненных сделок для AI-анализа. Нужно минимум 5 сделок с соблюдением плана, эмоцией и причиной.\':code===\'ai_daily_limit_reached\'?\'Дневной лимит AI на сегодня исчерпан.\':code===\'ai_too_many_requests\'?\'Слишком много AI-запросов подряд. Повтори немного позже.\':\'AI-анализ временно недоступен. Код: \'+code;out.innerHTML=\'<div class="aiout error">\'+esc(text)+\'</div>\'}}\n')
s = replace_block(s, "async function sendSupport()", "async function loadAdmin()", "async function sendSupport(){try{await call('submit_support',{category:'support',message:q('#smsg').value});msg(state.access&&state.access.isOwner?'Тестовое сообщение сохранено. Сообщения тестеров отображаются ниже в Owner Beta → Управление тестерами → Поддержка.':'Сообщение отправлено. Владелец PlanFact увидит его в разделе поддержки.',true)}catch(e){msg(e.code||e.message,false)}}\n")
s = replace_block(s, "async function loadAdmin()", "async function setBeta(", 'async function loadAdmin(){var box=q(\'#admin\');box.innerHTML=\'<p class="muted">Загрузка…</p>\';try{var d=(await call(\'beta_admin_dashboard\')).dashboard,users=d.users||[],feedback=d.feedback||[],userHtml=users.length?users.map(function(u){var key=String(u.accountCode||\'\').replace(/[^A-Z0-9]/g,\'\'),until=u.tier===\'beta_pro\'&&u.accessUntil?\'<div class="success">Beta Pro до \'+esc(fmtDate(u.accessUntil))+\'</div>\':\'<div class="muted">Текущий доступ: Base</div>\';return\'<div class="user"><div class="between"><b>\'+esc(u.accountCode)+\'</b><span class="pill">\'+esc(u.tier)+\'</span></div>\'+until+\'<div class="muted">Сделок \'+u.tradeCount+\' · Планов \'+u.planCount+\' · AI \'+u.aiCount+\'</div><div class="two" style="margin-top:8px"><input id="days_\'+key+\'" type="number" min="1" max="365" inputmode="numeric" value="28" placeholder="Дней"><button class="btn small" onclick="grantCustom(&quot;\'+esc(u.accountCode)+\'&quot;)">Выдать Beta Pro</button></div><div class="row"><button class="btn small danger" onclick="setBeta(&quot;\'+esc(u.accountCode)+\'&quot;,1,false,false)">Вернуть Base</button><button class="btn small danger" onclick="blockUser(&quot;\'+esc(u.accountCode)+\'&quot;,\'+(u.status===\'blocked\'?\'false\':\'true\')+\')">\'+(u.status===\'blocked\'?\'Разблокировать\':\'Блокировать\')+\'</button></div></div>\'}).join(\'\'):\'<div class="empty">Других пользователей пока нет.</div>\',supportHtml=\'<h2 style="margin-top:18px">Поддержка</h2>\'+(feedback.length?feedback.map(function(f){return\'<div class="user"><div class="between"><b>\'+esc(f.accountCode)+\'</b><span class="pill">\'+esc(f.status||\'open\')+\'</span></div><div class="muted">\'+esc(fmtDate(f.createdAt))+\' · \'+esc(f.category||\'support\')+\'</div><p>\'+esc(f.message)+\'</p></div>\'}).join(\'\'):\'<div class="empty">Сообщений от тестеров пока нет.</div>\');box.innerHTML=userHtml+supportHtml}catch(e){box.innerHTML=\'<p class="error">\'+esc(e.code||e.message)+\'</p>\'}}\nasync function grantCustom(c){var key=String(c||\'\').replace(/[^A-Z0-9]/g,\'\'),el=q(\'#days_\'+key),days=Number(el&&el.value);if(!Number.isInteger(days)||days<1||days>365){alert(\'Укажи срок от 1 до 365 дней\');return}await setBeta(c,days,false,true)}\n')

if not s.lstrip().lower().startswith("<!doctype html>"):
    raise SystemExit("source is not HTML")
if "BETA 0.8" not in s or "PlanFact Beta 0.8" not in s:
    raise SystemExit("unexpected Beta version")
if gateway not in s or direct in s:
    raise SystemExit("gateway replacement failed")
if 'id="fdate"' in s or "Навсегда" in s:
    raise SystemExit("old Beta controls still present")
if "Сначала новые" not in s or "grantCustom" not in s:
    raise SystemExit("Beta 0.8 UX patch missing")

p.write_text(s, encoding="utf-8")

js_start = s.rfind("<script>")
js_end = s.rfind("</script>")
if js_start < 0 or js_end <= js_start:
    raise SystemExit("inline app script not found")
app_js = p.with_suffix(".check.js")
app_js.write_text(s[js_start + len("<script>"):js_end], encoding="utf-8")
try:
    subprocess.run(["node", "--check", str(app_js)], check=True)
finally:
    app_js.unlink(missing_ok=True)

print("Beta build validation passed")
