const $ = id => document.getElementById(id);
let socket, sequence = 0, polling = false;
const pending = new Map();
function rpc(method) {
  return new Promise((resolve, reject) => {
    if (!socket || socket.readyState !== WebSocket.OPEN) return reject(new Error('로봇 연결을 확인해 주세요.'));
    const id = ++sequence;
    const timer = setTimeout(() => { pending.delete(id); reject(new Error('응답이 늦어지고 있어요. 잠시 후 다시 시도해 주세요.')); }, 12000);
    pending.set(id, {resolve, reject, timer});
    socket.send(JSON.stringify({jsonrpc:'2.0', id, method, params:{}}));
  });
}
function render(s) {
  const names = {idle:'시작 전',intake:`질문 ${s.index+1} / 3`,smalltalk:'스몰토크',stopped:'대화 종료'};
  $('phase').textContent = names[s.phase] || '준비 중';
  $('connection').textContent = s.backend_ready && s.speech_ready ? '● 연결 완료' : '연결 확인 중';
  $('question').textContent = s.question || ({idle:'준비되셨다면 시작해 주세요.',smalltalk:'문진이 끝났어요. 편하게 이야기해요.',stopped:'다시 이야기하고 싶으면 시작해 주세요.'}[s.phase] || '준비 중');
  $('listening').textContent = s.turn === 'speaking' ? '리치 미니가 이야기하고 있어요' : s.turn === 'thinking' ? '답변을 준비하고 있어요' : ['intake','smalltalk'].includes(s.phase) ? '듣고 있어요 · 답변 뒤 잠시 기다려 주세요' : '';
  $('error').textContent = s.error || '';
  $('start').disabled = !s.backend_ready || !s.speech_ready || ['speaking','thinking'].includes(s.turn);
  $('stop').disabled = !['intake','smalltalk'].includes(s.phase);
  $('start').textContent = s.phase === 'idle' ? '문진 시작' : '다시 시작';
  [...$('steps').children].forEach((el,i) => {el.className = i < s.index ? 'done' : s.phase === 'intake' && i === s.index ? 'active' : '';});
}
async function poll() {
  if (polling) return;
  polling = true;
  try { render(await rpc('intake.status')); }
  catch(e) { $('error').textContent = e.message; }
  finally { polling = false; }
}
function connect() {
  socket = new WebSocket(`${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${location.host}/rpc`);
  socket.onopen = poll;
  socket.onmessage = event => {
    const message = JSON.parse(event.data);
    if (pending.has(message.id)) {
      const job = pending.get(message.id); pending.delete(message.id); clearTimeout(job.timer);
      if (message.error) job.reject(new Error(message.error.message)); else job.resolve(message.result);
    }
    if (message.method === 'conversation.transcript' && message.params.final) {
      $('last-message').textContent = `${message.params.role === 'user' ? '나' : '리치 미니'} · ${message.params.text}`;
      poll();
    }
  };
  socket.onclose = () => {
    $('connection').textContent = '연결이 끊겼어요'; $('start').disabled = true; $('stop').disabled = true;
    for (const job of pending.values()) {clearTimeout(job.timer); job.reject(new Error('로봇에 다시 연결하고 있어요.'));}
    pending.clear(); setTimeout(connect, 2000);
  };
}
for (const [id,method] of [['start','intake.start'],['stop','intake.stop']]) {
  $(id).onclick = async () => {
    $(id).disabled = true;
    try {await rpc(method); $('last-message').textContent = id === 'start' ? '새 문진을 시작합니다.' : '대화를 종료했습니다.'; await poll();}
    catch(e) {$('error').textContent = e.message;}
  };
}
connect(); setInterval(poll, 2500);
