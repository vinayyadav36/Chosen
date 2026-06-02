const interview = JSON.parse(sessionStorage.getItem('interview') || '{}');
const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
const socket = new WebSocket(`${protocol}://${window.location.host}/api/interview/${interview.interview_id}/voice-stream`);
const statusEl = document.getElementById('status');
const progress = document.getElementById('progress');
const transcript = document.getElementById('transcript');
const micBtn = document.getElementById('mic-btn');
const endBtn = document.getElementById('end-btn');
const audio = document.getElementById('tts-player');

function row(text) {
  const div = document.createElement('div');
  div.className = 'row';
  div.textContent = text;
  transcript.appendChild(div);
  transcript.scrollTop = transcript.scrollHeight;
}

socket.onopen = () => { statusEl.textContent = 'Connected'; };
socket.onclose = () => { statusEl.textContent = 'Disconnected'; };

socket.onmessage = (event) => {
  const payload = JSON.parse(event.data);
  if (payload.type === 'question') {
    row(`AI: ${payload.text}`);
    progress.textContent = `Question ${payload.question_number}/${payload.total_questions}`;
  }
  if (payload.type === 'transcript') row(`You: ${payload.text}`);
  if (payload.type === 'status') statusEl.textContent = payload.state;
  if (payload.type === 'audio' && payload.data) {
    const bytes = atob(payload.data);
    const array = new Uint8Array(bytes.length);
    for (let i = 0; i < bytes.length; i += 1) array[i] = bytes.charCodeAt(i);
    audio.src = URL.createObjectURL(new Blob([array], { type: 'audio/mpeg' }));
    audio.play().catch(() => {});
  }
  if (payload.type === 'completed') {
    row('Interview complete. Redirecting...');
    setTimeout(() => window.location.href = `/frontend/report.html?id=${interview.interview_id}`, 1000);
  }
};

micBtn?.addEventListener('click', () => {
  const sample = new TextEncoder().encode('I built scalable FastAPI services with MongoDB and Docker');
  socket.send(sample);
});

endBtn?.addEventListener('click', () => {
  socket.send(JSON.stringify({ type: 'stop' }));
  socket.close();
});
