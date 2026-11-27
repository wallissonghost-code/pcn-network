// Public visual preview only. No API, accounts, credentials or financial assets.
const $=id=>document.getElementById(id);
const state={active:false,claimed:false,ends:0,balance:0,history:[]};
function msg(value){$('message').textContent=value}
function showDashboard(){ $('auth').hidden=true;$('dashboard').hidden=false;render() }
function render(){
 $('balance').textContent=state.balance.toLocaleString('pt-BR',{minimumFractionDigits:2});
 $('session').textContent=state.active?'Sessão demonstrativa em andamento.':'Nenhuma sessão ativa. Inicie uma demonstração.';
 $('referrals').textContent='Código: PCN-DEMO • Convites fictícios: 0';
 $('history').replaceChildren();
 if(!state.history.length)$('history').textContent='Nenhuma recompensa registrada.';
 for(const item of state.history){const div=document.createElement('div');div.textContent=item;$('history').append(div)}
 $('admin').hidden=true;
}
$('network').textContent='Rede de demonstração • Estatísticas fictícias • Nenhuma moeda real';
$('email').disabled=true;$('password').disabled=true;$('referral').disabled=true;
for(const action of ['login','register'])$(action).onclick=()=>{showDashboard();msg('Modo demonstração: nenhum cadastro foi criado.')};
$('start').onclick=()=>{
 if(state.active){msg('Já existe uma sessão demonstrativa ativa.');return}
 state.active=true;state.claimed=false;state.ends=Date.now()+86400000;
 render();msg('Sessão demonstrativa iniciada. Para visualizar o resgate, use o botão Resgatar recompensa.')
};
$('claim').onclick=()=>{
 if(!state.active){msg('Ative a sessão demonstrativa primeiro.');return}
 state.active=false;state.claimed=true;state.balance+=2.4;
 state.history.unshift('+2,40 PCN • recompensa fictícia');
 render();msg('Resgate de demonstração: +2,40 PCN fictícios. Na aplicação real, é necessário esperar 24 horas.')
};
$('copy-referral').onclick=async()=>{try{await navigator.clipboard.writeText('PCN-DEMO');msg('Código fictício copiado')}catch(e){msg('Código fictício: PCN-DEMO')}};
$('logout').onclick=()=>{$('dashboard').hidden=true;$('auth').hidden=false;msg('Demonstração encerrada.')};
msg('Prévia pública: os dados existem somente nesta página e não são salvos.');
