const $=id=>document.getElementById(id);let token=sessionStorage.getItem('pcn_token');
async function api(path,body){const res=await fetch('/api/'+path,{method:body===undefined?'GET':'POST',headers:{'Content-Type':'application/json',...(token?{Authorization:'Bearer '+token}:{})},...(body!==undefined?{body:JSON.stringify(body)}:{})});const data=await res.json();if(!res.ok){const error=new Error(data.error||'Falha na operação');error.status=res.status;throw error}return data}
function msg(t){$('message').textContent=t}
async function network(){try{const n=await api('network');$('network').textContent=n.users+' participantes • '+n.active_sessions+' sessões ativas • '+n.issued_pcn.toLocaleString('pt-BR')+' PCN simulados emitidos'}catch(e){$('network').textContent='Indicadores temporariamente indisponíveis'}}
let referralCode='';$('copy-referral').onclick=async()=>{if(!referralCode)return;try{await navigator.clipboard.writeText(referralCode);msg('Código copiado')}catch(e){msg('Código: '+referralCode)}};
async function refresh(){
 if(!token){$('auth').hidden=false;$('dashboard').hidden=true;return}
 let s;
 try{s=await api('status')}
 catch(e){
  if(e.status===401){token=null;sessionStorage.removeItem('pcn_token');$('auth').hidden=false;$('dashboard').hidden=true;msg('Sessão expirada. Entre novamente.')}
  else msg('Não foi possível atualizar o saldo: '+e.message);
  return;
 }
 $('auth').hidden=true;$('dashboard').hidden=false;
 $('balance').textContent=s.balance.toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:6});
 const x=s.session;
 $('session').textContent=!x?'Nenhuma sessão iniciada.':x.claimed?'Sessão resgatada. Você pode iniciar outra.':Date.now()/1000<x.ends?'Mineração ativa até '+new Date(x.ends*1000).toLocaleString('pt-BR'):'Sessão concluída! Resgate sua recompensa.';
 $('history').replaceChildren();
 if(!s.history.length)$('history').textContent='Nenhuma recompensa registrada.';
 for(const h of s.history){const div=document.createElement('div');div.textContent='+'+h.amount.toLocaleString('pt-BR')+' PCN • '+new Date(h.created*1000).toLocaleString('pt-BR');$('history').append(div)}
 try{
  const ref=await api('referrals');referralCode=ref.code;
  $('referrals').textContent='Código: '+ref.code+' • Convites cadastrados: '+ref.invited_count;
 }catch(e){$('referrals').textContent='Indicações temporariamente indisponíveis'}
 $('admin').hidden=true;
 try{
  const access=await api('admin/access');
  if(access.admin){
   $('admin').hidden=false;
   const stats=await api('admin/stats');
   const fmt=n=>Number(n).toLocaleString('pt-BR');
   $('admin-stats').replaceChildren();
   for(const [label,key] of [['Usuários','users'],['Sessões ativas','active_sessions'],['Sessões a resgatar','unclaimed_sessions'],['Indicações','referrals'],['PCN emitidos','issued_pcn'],['PCN restantes','remaining_pcn'],['PCN emitidos hoje (UTC)','today_issued_pcn'],['Tentativas de autenticação (15 min)','recent_auth_attempts']]){
    const p=document.createElement('p');p.textContent=label+': '+fmt(stats[key]);$('admin-stats').append(p)
   }
  }
 }catch(e){if(!$('admin').hidden)$('admin-stats').textContent='Estatísticas administrativas temporariamente indisponíveis'}
}
for(const action of ['login','register'])$(action).onclick=async()=>{try{const r=await api(action,{email:$('email').value,password:$('password').value,...(action==='register'?{referral:$('referral').value}:{})});token=r.token;sessionStorage.setItem('pcn_token',token);msg('Autenticado.');refresh()}catch(e){msg(e.message)}};
for(const action of ['start','claim'])$(action).onclick=async()=>{try{const r=await api(action,{});msg(r.message||'Recompensa resgatada: '+r.claimed+' PCN');refresh()}catch(e){msg(e.message)}};
$('logout').onclick=async()=>{try{await api('logout',{})}catch(e){}token=null;sessionStorage.removeItem('pcn_token');msg('Sessão encerrada.');refresh()};refresh();network();