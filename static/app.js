// Private premium integration. Server is authoritative; no local balance or reward mutations.
const $=id=>document.getElementById(id);
let token=sessionStorage.getItem('pcn_token')||'';
let status=null;
let busy=false;
const headings={home:'Visão geral',mine:'Mineração',wallet:'Minha carteira',network:'Ecossistema'};
const CYCLE_MS=86400000;
function toast(message){const el=$('toast');el.textContent=message;el.classList.add('show');clearTimeout(toast.timer);toast.timer=setTimeout(()=>el.classList.remove('show'),4500)}
async function api(path,body){
 const res=await fetch('/api/'+path,{method:body===undefined?'GET':'POST',headers:{...(body===undefined?{}:{'Content-Type':'application/json'}),...(token?{Authorization:'Bearer '+token}:{})},...(body===undefined?{}:{body:JSON.stringify(body)})});
 let data;try{data=await res.json()}catch{throw new Error('Resposta inválida do servidor')}
 if(!res.ok){const error=new Error(data.error||'Operação indisponível');error.status=res.status;throw error}
 return data;
}
function go(tab){if(!headings[tab])return;document.querySelectorAll('.page').forEach(el=>el.classList.toggle('active',el.id===tab));document.querySelectorAll('[data-tab]').forEach(el=>el.classList.toggle('active',el.dataset.tab===tab));$('page-heading').textContent=headings[tab];window.scrollTo({top:0,behavior:'smooth'})}
document.querySelectorAll('[data-tab]').forEach(el=>el.addEventListener('click',()=>go(el.dataset.tab)));
function gate(authorized,message=''){
 $('auth-gate').hidden=authorized;$('authenticated-app').hidden=!authorized;
 $('auth-message').textContent=message;
 $('logout-session').hidden=!authorized;
}
function progress(){
 const s=status?.session;
 const running=!!s&&!s.claimed;
 const remaining=running?Math.max(0,s.ends*1000-Date.now()):CYCLE_MS;
 const percent=running?Math.min(100,Math.max(0,(CYCLE_MS-remaining)/CYCLE_MS*100)):0;
 const h=Math.floor(remaining/3600000),m=Math.floor((remaining%3600000)/60000);
 const label=running&&remaining===0?'Ciclo concluído':h+'h '+String(m).padStart(2,'0')+'m restantes';
 for(const prefix of ['home','mine']){$(prefix+'-progress-fill').style.width=percent.toFixed(2)+'%';$(prefix+'-progress').setAttribute('aria-valuenow',String(Math.round(percent)));$(prefix+'-progress-percent').textContent=percent.toFixed(1).replace('.',',')+'%'}
 $('home-remaining').textContent=label;$('mine-remaining').textContent=label;
 const ready=running&&remaining===0;
 $('mine-badge').textContent=ready?'RESGATE DISPONÍVEL':running?'EM ANDAMENTO':'DISPONÍVEL';
 $('mine-badge').classList.toggle('running',running);
 document.querySelectorAll('.orb-wrap').forEach(el=>el.classList.toggle('is-mining',running&&!ready));
 $('mining-status').textContent=ready?'Recompensa disponível':running?'Sessão em andamento':'Pronto para começar';
 $('mining-sub').textContent=running?label:'Ative seu ciclo de 24 horas';
 $('mine-page-status').textContent=ready?'Ciclo concluído!':running?'Mineração ativa':'Pronto para minerar';
 $('mine-page-detail').textContent=running?label:'Inicie uma sessão de 24 horas controlada pelo servidor.';
 $('mine-action').textContent=ready?'Resgatar recompensa ↗':running?'Mineração em andamento':'Iniciar mineração ↗';
 $('mine-page-action').textContent=ready?'Resgatar recompensa ↗':running?'Aguardar conclusão':'Iniciar ciclo de 24 horas ↗';
 $('mine-action').disabled=busy||(running&&!ready);$('mine-page-action').disabled=busy||(running&&!ready);
}
function render(){
 if(!status)return;
 const number=Number(status.balance).toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:6});
 $('balance-main').textContent=number;$('wallet-balance').textContent=number;
 const list=$('transactions');list.replaceChildren();
 if(!status.history.length){const el=document.createElement('div');el.className='empty-state';el.textContent='Nenhuma recompensa registrada.';list.append(el)}
 for(const entry of status.history){const el=document.createElement('div');el.className='transaction';const left=document.createElement('div');const name=document.createElement('strong');name.textContent='Recompensa de mineração';const date=document.createElement('small');date.textContent=new Date(entry.created*1000).toLocaleString('pt-BR');left.append(name,date);const amount=document.createElement('span');amount.className='positive';amount.textContent='+'+Number(entry.amount).toLocaleString('pt-BR')+' PCN';el.append(left,amount);list.append(el)}
 progress();
}
async function refresh(){
 if(!token){status=null;gate(false);return}
 try{
  const [session,s]=await Promise.all([api('session'),api('status')]);
  if(!session.authenticated)throw Object.assign(new Error('Sessão expirada'),{status:401});
  status=s;gate(true);render();
  try{const ref=await api('referrals');$('copy-code').textContent=ref.code+' ⧉';$('copy-code').dataset.code=ref.code}catch{$('copy-code').textContent='Indisponível'}
 }catch(e){
  if(e.status===401){token='';sessionStorage.removeItem('pcn_token');status=null;gate(false,'Sessão expirada. Entre novamente.')}
  else{gate(!!status);toast('Falha ao consultar o servidor: '+e.message)}
 }
}
$('auth-form').addEventListener('submit',async e=>{
 e.preventDefault();if(busy)return;busy=true;const btn=$('auth-form').querySelector('button');btn.disabled=true;
 try{const r=await api('login',{email:$('auth-email').value,password:$('auth-password').value});token=r.token;sessionStorage.setItem('pcn_token',token);$('auth-password').value='';await refresh();toast('Sessão de teste iniciada.')}
 catch(e){$('auth-message').textContent=e.message}
 finally{busy=false;btn.disabled=false}
});
async function mine(){
 if(busy||!status)return;const s=status.session;const ready=!!s&&!s.claimed&&Date.now()>=s.ends*1000;
 if(s&&!s.claimed&&!ready)return;
 busy=true;progress();
 try{const result=await api(ready?'claim':'start',{});toast(ready?'Recompensa registrada pelo servidor: '+result.claimed+' PCN':'Ciclo de 24 horas iniciado.');await refresh()}
 catch(e){toast(e.message);await refresh()}
 finally{busy=false;progress()}
}
$('mine-action').addEventListener('click',mine);$('mine-page-action').addEventListener('click',mine);
$('reset-demo').addEventListener('click',refresh);
$('copy-code').addEventListener('click',async()=>{const code=$('copy-code').dataset.code;if(!code)return;try{await navigator.clipboard.writeText(code);toast('Código copiado.')}catch{toast('Código: '+code)}});
$('logout-session').addEventListener('click',async()=>{try{if(token)await api('logout',{})}catch{}token='';status=null;sessionStorage.removeItem('pcn_token');gate(false,'Sessão encerrada.');go('home')});
gate(false);refresh();setInterval(()=>{if(status)progress()},15000);
