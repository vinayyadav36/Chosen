const params = new URLSearchParams(window.location.search);
const idInput = document.getElementById('interview-id');
const reportEl = document.getElementById('report');
const pdfLink = document.getElementById('pdf-link');
const loadBtn = document.getElementById('load-btn');

idInput.value = params.get('id') || '';

async function load() {
  const id = idInput.value.trim();
  if (!id) return;
  const response = await fetch(`/api/interview/${id}/report`);
  const payload = await response.json();
  reportEl.textContent = JSON.stringify(payload, null, 2);
  if (payload.pdf_url) {
    pdfLink.href = payload.pdf_url;
    pdfLink.style.display = 'inline-block';
  }
}

loadBtn?.addEventListener('click', load);
if (idInput.value) load();
