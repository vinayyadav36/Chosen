const interview = JSON.parse(sessionStorage.getItem('interview') || '{}');
const chat = document.getElementById('chat');
const form = document.getElementById('chat-form');
const messageInput = document.getElementById('message');
const progress = document.getElementById('progress');

function bubble(text, cls) {
  const div = document.createElement('div');
  div.className = `bubble ${cls}`;
  div.textContent = text;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

form?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const message = messageInput.value.trim();
  if (!message) return;
  bubble(message, 'candidate');
  messageInput.value = '';

  const response = await fetch(`/api/interview/${interview.interview_id}/text-message`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  });
  const payload = await response.json();
  if (!response.ok) {
    bubble(payload.error || 'Failed to send message', 'ai');
    return;
  }

  if (payload.question) bubble(payload.question, 'ai');
  progress.textContent = `Question ${payload.question_number}/${payload.total_questions}`;

  if (payload.is_complete) {
    bubble('Interview complete. Redirecting to report...', 'ai');
    setTimeout(() => {
      window.location.href = `/frontend/report.html?id=${interview.interview_id}`;
    }, 900);
  }
});
