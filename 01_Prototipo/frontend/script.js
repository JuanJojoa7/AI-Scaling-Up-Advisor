let token = localStorage.getItem('advisor_token') || null;
let sessionId = localStorage.getItem('advisor_session') ? parseInt(localStorage.getItem('advisor_session')) : null;
let questions = [];
let answers = JSON.parse(localStorage.getItem('advisor_answers') || '[]');
let chatLog = JSON.parse(localStorage.getItem('advisor_chatlog') || '[]');
let currentQId = null;

function show(id){ document.getElementById(id).classList.remove('hidden'); }
function hide(id){ document.getElementById(id).classList.add('hidden'); }
function msg(text, who){
  const qa = document.getElementById('qa');
  // evita duplicados consecutivos del bot con el mismo texto
  const last = qa.lastElementChild;
  if(last && last.classList.contains('bot') && last.textContent === text && who === 'bot'){
    return;
  }
  const div = document.createElement('div');
  div.className = 'msg ' + who;
  div.textContent = text;
  qa.appendChild(div);
  // scroll suave y mantener foco en el input
  try { div.scrollIntoView({behavior:'smooth', block:'end'}); } catch{}
  const box = document.getElementById('answerBox');
  if(box){ box.focus(); }
  chatLog.push({who, text});
  localStorage.setItem('advisor_chatlog', JSON.stringify(chatLog));
}

function resetToAuth(){
  hide('chat'); hide('results'); hide('onboarding'); show('auth');
  token = null; localStorage.removeItem('advisor_token');
  authMsg.textContent = 'Sesión expirada. Inicia nuevamente.';
  const userBar = document.getElementById('userBar'); if(userBar) userBar.classList.add('hidden');
}

async function api(path, method='GET', body=null){
  const opts = { method, headers: { 'Content-Type':'application/json' } };
  if(token) opts.headers['Authorization'] = 'Bearer ' + token;
  if(body) opts.body = JSON.stringify(body);
  let r;
  try { r = await fetch('http://127.0.0.1:8000' + path, opts); }
  catch(err){ console.error('Network error', err); throw new Error('Error de red'); }
  if(r.status === 401){ resetToAuth(); throw new Error('No autorizado'); }
  if(!r.ok){ let txt = await r.text(); console.error('API error', r.status, txt); throw new Error(txt || ('Error '+r.status)); }
  return r.json();
}

function nextQuestion(){
  const remaining = questions.filter(q => !answers.find(a => a.question_id === q.id));
  if(remaining.length === 0){
    hide('chat');
    show('results');
    refreshSummary();
    return;
  }
  const q = remaining[0];
  if(currentQId !== q.id){
    msg(q.text, 'bot');
    currentQId = q.id;
  }
  const box = document.getElementById('answerBox');
  box.value = '';
  box.placeholder = q.type === 'number' ? 'Ingresa número' : 'Tu respuesta...';
  box.dataset.qid = q.id;
  box.dataset.module = q.module;
  if(q.type === 'multi'){
    box.value = '';
    box.placeholder = 'Opciones: ' + q.options.join(', ');
  }
  box.focus();
}

async function refreshSummary(){
  try{
    const r = await api('/api/reports/summary','POST',{session_id: sessionId});
    const quick = document.getElementById('quickSummary');
    if(quick){
      const p = r.priorities || [];
      const rec = r.recommendations || [];
      quick.innerHTML = `
        <div style="margin-bottom:8px;">${(r.summary||'').replace(/\n/g,'<br/>')}</div>
        <div style="display:grid; gap:8px; grid-template-columns: repeat(auto-fit,minmax(220px,1fr));">
          <div>
            <strong>Top 3 prioridades</strong>
            <ol>${p.slice(0,3).map(x=>`<li>${x}</li>`).join('')}</ol>
          </div>
          <div>
            <strong>Acciones sugeridas</strong>
            <ul>${rec.slice(0,3).map(x=>`<li>${x}</li>`).join('')}</ul>
          </div>
        </div>`;
    }
  }catch(e){
    const quick = document.getElementById('quickSummary');
    if(quick){ quick.textContent = 'No se pudo generar el resumen rápido en este momento.'; }
  }
}

// Auth
btnRegister.onclick = async () => {
  try {
    const r = await api('/api/auth/register','POST',{email:email.value,password:password.value});
  token = r.access_token; localStorage.setItem('advisor_token', token); localStorage.setItem('advisor_email', email.value); authMsg.textContent = 'Registrado'; postAuth();
  } catch(e){ authMsg.textContent = 'Error: '+e.message; }
};
btnLogin.onclick = async () => {
  try {
    const r = await api('/api/auth/login','POST',{email:email.value,password:password.value});
  token = r.access_token; localStorage.setItem('advisor_token', token); localStorage.setItem('advisor_email', email.value); authMsg.textContent = 'Login OK'; postAuth();
  } catch(e){ authMsg.textContent = 'Error: '+e.message; }
};

async function postAuth(){
  hide('auth'); show('onboarding');
  const ob = await api('/api/diagnosis/onboarding');
  intro.innerHTML = `<p>${ob.intro}</p><ul>${ob.steps.map(s=>'<li>'+s+'</li>').join('')}</ul>`;
  // cargar listado de sesiones del usuario
  await loadSessions();
  show('sessions');
  // mostrar user bar
  const userBar = document.getElementById('userBar');
  const userEmail = document.getElementById('userEmail');
  if(userBar && userEmail){
    const savedEmail = localStorage.getItem('advisor_email') || email.value || 'Usuario';
    userEmail.textContent = savedEmail;
    userBar.classList.remove('hidden');
  }
}

btnStart.onclick = async () => {
  try {
    const s = await api('/api/diagnosis/start','POST');
    sessionId = s.session_id; localStorage.setItem('advisor_session', String(sessionId));
    questions = await api('/api/diagnosis/questions');
    hide('onboarding'); hide('sessions'); show('chat');
    msg('Sesión iniciada. Responde cada pregunta.','bot');
    nextQuestion();
  } catch(e){ msg('Error iniciando: '+e.message,'bot'); if(e.message.includes('No autorizado')) resetToAuth(); }
};

btnSend.onclick = async () => {
  const box = document.getElementById('answerBox');
  const qid = box.dataset.qid; const module = box.dataset.module; const q = questions.find(q=>q.id===qid);
  let value = box.value.trim();
  if(!value){ msg('Ingresa una respuesta.','bot'); return; }
  if(q.type==='number'){ value = parseFloat(value); if(isNaN(value)){ msg('Número inválido','bot'); return; } }
  answers.push({ question_id: qid, module, value });
  localStorage.setItem('advisor_answers', JSON.stringify(answers));
  msg(value,'user');
  try { await api('/api/diagnosis/answer','POST',{ session_id: sessionId, question_id: qid, module, value }); } catch(e){ msg('Error guardando: '+e.message,'bot'); if(e.message.includes('No autorizado')) resetToAuth(); return; }
  nextQuestion();
};

btnReport.onclick = async () => {
  try {
    const r = await api('/api/reports/generate','POST',{session_id: sessionId});
    // Mantener visible el resumen
    reportPreview.innerHTML = `
      <h3>Prioridades</h3>
      <ul>${(r.priorities||[]).map(p=>'<li>'+p+'</li>').join('')}</ul>
      <h3>Recomendaciones</h3>
      <ul>${(r.recommendations||[]).map(p=>'<li>'+p+'</li>').join('')}</ul>
      <p>
        <a id="pdfLink" href="http://127.0.0.1:8000${r.pdf_url}" target="_blank">Abrir PDF</a>
      </p>`;
    // Disparar la apertura del PDF para que el navegador permita guardar en Descargar
    setTimeout(()=>{
      const a = document.getElementById('pdfLink');
      if(a){ a.click(); }
    }, 200);
  } catch(e){ msg('Error generando informe: '+e.message,'bot'); if(e.message.includes('No autorizado')) resetToAuth(); }
};

async function tryAutoResume(){
  if(token && sessionId){
    try {
      const r = await api(`/api/diagnosis/resume/${sessionId}`);
      if(r && Array.isArray(r.answers)){
        answers = r.answers; localStorage.setItem('advisor_answers', JSON.stringify(answers));
      }
      questions = await api('/api/diagnosis/questions');
      hide('onboarding'); hide('sessions'); show('chat');
      document.getElementById('qa').innerHTML = '';
      rebuildChatFromAnswers();
      nextQuestion();
    } catch(e){ console.warn('Resume falló', e.message); }
  }
}

if(token){
  postAuth().then(()=>{ tryAutoResume(); });
}

// ===================== Sesiones =====================
async function loadSessions(){
  let listDiv = document.getElementById('sessionsList');
  let sel = document.getElementById('sessionSelect');
  const err = document.getElementById('sessionsError');
  listDiv.innerHTML = '';
  err.textContent = 'Cargando sesiones...';
  try {
    const data = await api('/api/diagnosis/sessions');
    renderSessions(data.sessions || []);
    // llenar combo
    if(sel){
      const sessions = data.sessions || [];
      sel.innerHTML = '';
      const opt0 = document.createElement('option');
      opt0.text = 'Selecciona una sesión...';
      opt0.value = '';
      sel.appendChild(opt0);
      sessions.forEach(s=>{
        const status = s.status === 'completed' ? 'Completada' : (s.answers_count > 0 ? 'En progreso' : 'Nueva');
        const lbl = `#${s.id} · ${status} · resp ${s.answers_count}`;
        const o = document.createElement('option');
        o.value = String(s.id); o.text = lbl;
        sel.appendChild(o);
      });
    }
    err.textContent = '';
  } catch(e){
    err.textContent = 'No pude cargar sesiones. Verifica que el servidor esté ejecutándose.';
  }
}

function renderSessions(sessions){
  const listDiv = document.getElementById('sessionsList');
  if(!sessions.length){ listDiv.innerHTML = '<p>No hay sesiones todavía.</p>'; return; }
  const fmt = (iso)=>{ try { return new Date(iso).toLocaleString(); } catch{ return iso; } };
  listDiv.innerHTML = '';
  sessions.forEach(s=>{
    const card = document.createElement('div');
    card.className = 'session-card';
    const status = s.status === 'completed' ? 'Completada' : (s.answers_count > 0 ? 'En progreso' : 'Nueva');
    card.innerHTML = `
      <h4>Sesión #${s.id}</h4>
      <div class="meta">Estado: ${status}<br/>Resp: ${s.answers_count} | Reporte: ${s.has_report ? 'Sí' : 'No'}<br/>Creada: ${fmt(s.created_at)}</div>
      <div class="actions">
        <button class="btnResume" data-id="${s.id}">Continuar</button>
      </div>
    `;
    listDiv.appendChild(card);
  });
  listDiv.querySelectorAll('.btnResume').forEach(btn=>{
    btn.onclick = ()=> resumeSession(parseInt(btn.dataset.id));
  });
}

async function resumeSession(id){
  try {
    sessionId = id; localStorage.setItem('advisor_session', String(sessionId));
    const r = await api(`/api/diagnosis/resume/${id}`);
    questions = await api('/api/diagnosis/questions');
    answers = r.answers || []; localStorage.setItem('advisor_answers', JSON.stringify(answers));
    hide('onboarding'); hide('sessions'); show('chat');
    document.getElementById('qa').innerHTML='';
    rebuildChatFromAnswers();
    nextQuestion();
  } catch(e){ msg('Error al reanudar: '+e.message,'bot'); }
}

function rebuildChatFromAnswers(){
  // Reinicia el chat log y lo reconstruye a partir de las respuestas guardadas
  chatLog = []; localStorage.setItem('advisor_chatlog', JSON.stringify(chatLog));
  answers.forEach(ans => {
    const q = questions.find(q=>q.id===ans.question_id);
    if(q){ msg(q.text,'bot'); msg(String(ans.value),'user'); }
  });
  if(answers.length === 0){ msg('Sesión recuperada. Comencemos.','bot'); }
  localStorage.setItem('advisor_chatlog', JSON.stringify(chatLog));
}

async function startNewSession(){
  try {
    const s = await api('/api/diagnosis/start','POST');
    sessionId = s.session_id; localStorage.setItem('advisor_session', String(sessionId));
    answers = []; localStorage.setItem('advisor_answers', JSON.stringify(answers));
    chatLog = []; localStorage.setItem('advisor_chatlog', JSON.stringify(chatLog));
    questions = await api('/api/diagnosis/questions');
    hide('onboarding'); hide('sessions'); show('chat');
    document.getElementById('qa').innerHTML='';
    nextQuestion();
  } catch(e){ msg('Error creando sesión: '+e.message,'bot'); }
}

// Botones de sesiones
const btnRefreshSessions = document.getElementById('btnRefreshSessions');
if(btnRefreshSessions){ btnRefreshSessions.onclick = loadSessions; }
const btnNewSession = document.getElementById('btnNewSession');
if(btnNewSession){ btnNewSession.onclick = startNewSession; }
const btnSelectSession = document.getElementById('btnSelectSession');
if(btnSelectSession){ btnSelectSession.onclick = () => {
  const sel = document.getElementById('sessionSelect');
  const val = sel && sel.value ? parseInt(sel.value) : null;
  if(val){ resumeSession(val); }
}; }
const btnBack = document.getElementById('btnBack');
if(btnBack){ btnBack.onclick = () => {
  // regresar al menú de sesiones sin perder token
  hide('chat'); hide('results'); show('onboarding'); show('sessions');
  currentQId = null;
  loadSessions();
}; }
const btnResultsBack = document.getElementById('btnResultsBack');
if(btnResultsBack){ btnResultsBack.onclick = () => {
  hide('results'); show('sessions'); show('onboarding');
  loadSessions();
}; }
const btnRefreshSummary = document.getElementById('btnRefreshSummary');
if(btnRefreshSummary){ btnRefreshSummary.onclick = refreshSummary; }
const btnLogout = document.getElementById('btnLogout');
if(btnLogout){ btnLogout.onclick = () => {
  // limpiar todo excepto interfaz de auth
  token = null; sessionId = null; answers = []; chatLog = [];
  localStorage.removeItem('advisor_token');
  localStorage.removeItem('advisor_session');
  localStorage.removeItem('advisor_answers');
  localStorage.removeItem('advisor_chatlog');
  localStorage.removeItem('advisor_email');
  document.getElementById('qa').innerHTML='';
  hide('chat'); hide('results'); hide('sessions'); show('auth');
  const userBar = document.getElementById('userBar'); if(userBar) userBar.classList.add('hidden');
  authMsg.textContent = 'Sesión cerrada.';
}; }
