// PCN public preview: local-only interactive simulation. No backend or real assets.
const $=id=>document.getElementById(id);
const state={balance:0,active:false,history:[]};
const headings={home:'Visão geral',mine:'Mineração',wallet:'Minha carteira',network:'Ecossistema'};
function toast(message){const el=$('toast');el.textContent=message;el.classList.add('show');clearTimeout(toast.timer);toast.timer=setTimeout(()=>el.classList.remove('show'),4000)}
function go(tab){if(!headings[tab])return;document.querySelectorAll('.page').forEach(el=>el.classList.toggle('active',el.id===tab));document.querySelectorAll('[data-tab]').forEach(el=>el.classList.toggle('active',el.dataset.tab===tab));$('page-heading').textContent=headings[tab];window.scrollTo({top:0,behavior:'smooth'})}
document.querySelectorAll('[data-tab]').forEach(el=>el.addEventListener('click',()=>go(el.dataset.tab)));
function render(){
 const number=state.balance.toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2});
 $('balance-main').textContent=number;$('wallet-balance').textContent=number;
 $('mine-badge').textContent=state.active?'EM ANDAMENTO':'DISPONÍVEL';
 $('mine-badge').classList.toggle('running',state.active);
 $('mining-status').textContent=state.active?'Sessão demonstrativa ativa':'Pronto para começar';
 $('mining-sub').textContent=state.active?'Recompensa fictícia disponível para teste':'Ative seu ciclo de 24 horas';
 $('mine-action').innerHTML=state.active?'Resgatar 2,40 PCN <span>↗</span>':'Iniciar mineração <span>↗</span>';
 $('mine-page-status').textContent=state.active?'Sessão ativada!':'Pronto para minerar';
 $('mine-page-detail').textContent=state.active?'Faça um resgate simulado para conhecer o fluxo.':'Ative sua sessão e explore a experiência de mineração.';
 $('mine-page-action').textContent=state.active?'Resgatar 2,40 PCN fictícios ↗':'Ativar sessão de demonstração ↗';
 const list=$('transactions');list.replaceChildren();
 if(!state.history.length){const el=document.createElement('div');el.className='empty-state';el.textContent='Nenhuma atividade ainda. Inicie uma mineração para experimentar.';list.append(el)}
 for(const entry of state.history){const el=document.createElement('div');el.className='transaction';const left=document.createElement('div');const name=document.createElement('strong');name.textContent='Recompensa de mineração';const date=document.createElement('small');date.textContent=entry.date;left.append(name,date);const amount=document.createElement('span');amount.className='positive';amount.textContent='+2,40 PCN';el.append(left,amount);list.append(el)}
}
function mine(){
 if(!state.active){state.active=true;toast('Ciclo demonstrativo ativado. Você já pode simular o resgate.')}
 else{state.active=false;state.balance=Math.round((state.balance+2.4)*100)/100;state.history.unshift({date:new Date().toLocaleString('pt-BR')+' · Demonstração'});toast('+2,40 PCN fictícios adicionados à carteira.')}
 render()
}
$('mine-action').addEventListener('click',mine);
$('mine-page-action').addEventListener('click',mine);
$('copy-code').addEventListener('click',async()=>{try{await navigator.clipboard.writeText('PCN-DEMO');toast('Código de demonstração copiado.')}catch{toast('Código de demonstração: PCN-DEMO')}});
render();
