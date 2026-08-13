from pathlib import Path
import re
import subprocess
import sys

p = Path(sys.argv[1] if len(sys.argv) > 1 else "site/index.html")
s = p.read_text(encoding="utf-8")
support_api = "https://vjglqivddspcolrzxmxt.supabase.co/functions/v1/planfact-beta-support"

# Add the dedicated Support/Bot boundary endpoint without changing the main Beta API.
marker = "var tg=window.Telegram&&window.Telegram.WebApp?window.Telegram.WebApp:null"
pos = s.find(marker)
if pos < 0:
    raise SystemExit("support patch: Telegram app marker missing")
prefix = s[:pos]
if "var SUPPORT_API=" not in prefix:
    prefix += f"var SUPPORT_API={support_api!r};\n"
s = prefix + s[pos:]

# Dedicated request helper. initData is still validated server-side for every support action.
anchor = "async function shotCall"
pos = s.find(anchor)
if pos < 0:
    raise SystemExit("support patch: shotCall marker missing")
helper = "async function supportCall(action,data){data=data||{};var body={action:action,init_data:init};Object.keys(data).forEach(function(k){body[k]=data[k]});var r=await fetch(SUPPORT_API,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});var b=await r.json().catch(function(){return{}});if(!r.ok||b.ok!==true){var e=new Error(b.error||'support_unavailable');e.code=b.error||'support_unavailable';throw e}return b}\n"
if "async function supportCall" not in s:
    s = s[:pos] + helper + s[pos:]

# Replace the user support modal and submission. The extra yellow warning is intentionally removed.
a = s.find("function supportModal()")
b = s.find("async function loadAdmin()", a)
if a < 0 or b <= a:
    raise SystemExit("support patch: support modal block missing")
replacement = "function supportModal(){modal('Поддержка','<textarea id=\"smsg\" placeholder=\"Опиши вопрос\"></textarea><button class=\"btn\" onclick=\"sendSupport()\">Отправить</button>')}async function sendSupport(){try{await supportCall('submit_support',{message:q('#smsg').value});msg('Сообщение отправлено',true)}catch(e){msg(e.code||e.message,false)}}\n"
s = s[:a] + replacement + s[b:]

# Main Beta dashboard remains responsible for tester access. Support tickets are loaded
# independently from the isolated support endpoint so raw Telegram identifiers never enter it.
pattern = re.compile(r"supportHtml=.*?;box\.innerHTML=userHtml\+supportHtml", re.S)
new_support = "supportHtml='<h2 style=\"margin-top:18px\">Поддержка</h2><div id=\"supportTickets\"><p class=\"muted\">Загрузка…</p></div>';box.innerHTML=userHtml+supportHtml;loadSupportTickets()"
s, count = pattern.subn(new_support, s, count=1)
if count != 1:
    raise SystemExit("support patch: Owner support section marker missing")

anchor = "async function grantCustom"
pos = s.find(anchor)
if pos < 0:
    raise SystemExit("support patch: grantCustom marker missing")
functions = r'''async function loadSupportTickets(){var box=q('#supportTickets');if(!box)return;box.innerHTML='<p class="muted">Загрузка…</p>';try{var d=await supportCall('list_support'),tickets=d.tickets||[];box.innerHTML=tickets.length?tickets.map(function(f){var key=String(f.ticketId||'').replace(/[^A-Za-z0-9]/g,''),closed=f.status==='closed';return'<div class="user"><div class="between"><b>'+esc(f.accountCode)+'</b><span class="pill">'+(closed?'закрыто':'открыто')+'</span></div><div class="muted">'+esc(fmtDate(f.createdAt))+' · '+esc(f.category||'support')+'</div><p>'+esc(f.message)+'</p>'+(closed?'<div class="card" style="margin:8px 0 0"><div class="muted">Ответ поддержки'+(f.repliedAt?' · '+esc(fmtDate(f.repliedAt)):'')+'</div><p style="margin-bottom:0">'+esc(f.ownerReply||'')+'</p></div>':'<textarea id="reply_'+key+'" placeholder="Напиши ответ пользователю"></textarea><button class="btn small" onclick="replySupport(&quot;'+esc(f.ticketId)+'&quot;)">Ответить</button>')+'</div>'}).join(''):'<div class="empty">Сообщений от тестеров пока нет.</div>'}catch(e){box.innerHTML='<p class="error">'+esc(e.code||e.message)+'</p>'}}
async function replySupport(ticketId){var key=String(ticketId||'').replace(/[^A-Za-z0-9]/g,''),el=q('#reply_'+key),text=String(el&&el.value||'').trim();if(!text){alert('Напиши ответ');return}try{await supportCall('reply_support',{ticket_id:ticketId,message:text});await loadSupportTickets()}catch(e){alert(e.code||e.message)}}
'''
if "async function loadSupportTickets" not in s:
    s = s[:pos] + functions + s[pos:]

if "Не отправляй API Secret, seed-фразы, коды подтверждения, ФИО, телефон или email." in s:
    raise SystemExit("support patch: old support warning still present")
if support_api not in s or "replySupport" not in s or "list_support" not in s:
    raise SystemExit("support patch validation failed")

p.write_text(s, encoding="utf-8")

js_start = s.rfind("<script>")
js_end = s.rfind("</script>")
if js_start < 0 or js_end <= js_start:
    raise SystemExit("support patch: inline app script missing")
check = p.with_suffix(".support-check.js")
check.write_text(s[js_start + len("<script>"):js_end], encoding="utf-8")
try:
    subprocess.run(["node", "--check", str(check)], check=True)
finally:
    check.unlink(missing_ok=True)

print("Support patch validation passed")
