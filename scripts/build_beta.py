from pathlib import Path
import subprocess
import sys

p = Path(sys.argv[1] if len(sys.argv) > 1 else "site/index.html")
s = p.read_text(encoding="utf-8")

direct = "https://vjglqivddspcolrzxmxt.supabase.co/functions/v1/planfact-beta-api"
gateway = "https://vjglqivddspcolrzxmxt.supabase.co/functions/v1/planfact-beta-gateway"
s = s.replace(direct, gateway)

# Fix malformed inline handlers generated in the temporary Beta frontend.
s = s.replace("onclick=\"nav(''+x[0]+'')\"", "onclick=\"nav(&quot;'+x[0]+'&quot;)\"")
s = s.replace("onclick=\"nav('plans')\"", "onclick=\"nav(&quot;plans&quot;)\"")
s = s.replace("onclick=\"removeTrade(''+esc(t.id)+'')\"", "onclick=\"removeTrade(&quot;'+esc(t.id)+'&quot;)\"")
s = s.replace("setBeta(''+u.accountCode+'',", "setBeta(&quot;'+u.accountCode+'&quot;,")
s = s.replace("blockUser(''+u.accountCode+'',", "blockUser(&quot;'+u.accountCode+'&quot;,")

# Replace the one block where escaped newlines were expanded into invalid JS strings.
start = s.find("async function runAI()")
end = s.find("function supportModal", start)
if start < 0 or end < 0:
    raise SystemExit("runAI block not found")
fixed_run_ai = r'''async function runAI(){var out=q('#aiout');out.innerHTML='<div class="aiout">Анализируем…</div>';try{var b=await call('analyze_discipline'),a=b.analysis||{},txt=(a.summary||'')+'\n\n'+(a.patterns||[]).map(function(p){return'• '+p.title+'\n'+p.evidence+'\nДействие: '+p.practicalAction}).join('\n\n')+'\n\nСледующий шаг: '+(a.nextStep||'');out.innerHTML='<div class="aiout">'+esc(txt)+'</div>'}catch(e){out.innerHTML='<div class="aiout error">'+esc(e.code||e.message)+'</div>'}}
'''
s = s[:start] + fixed_run_ai + s[end:]

if not s.lstrip().lower().startswith("<!doctype html>"):
    raise SystemExit("source is not HTML")
if "BETA 0.8" not in s or "PlanFact Beta 0.8" not in s:
    raise SystemExit("unexpected Beta version")
if gateway not in s or direct in s:
    raise SystemExit("gateway replacement failed")

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
