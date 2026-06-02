const form = document.getElementById('start-form');
const statusEl = document.getElementById('status');

form?.addEventListener('submit', async (event) => {
  event.preventDefault();
  statusEl.textContent = 'Starting interview...';
  const data = new FormData(form);
  const response = await fetch('/api/interview/start', { method: 'POST', body: data });
  const payload = await response.json();
  if (!response.ok) {
    statusEl.textContent = payload.error || 'Failed to start interview';
    return;
  }
  sessionStorage.setItem('interview', JSON.stringify(payload));
  const target = payload.mode === 'voice' ? '/frontend/voice-interview.html' : '/frontend/text-interview.html';
  window.location.href = target;
});
