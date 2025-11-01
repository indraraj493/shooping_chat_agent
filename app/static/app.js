const chatEl = document.getElementById('chat');
const formEl = document.getElementById('chat-form');
const inputEl = document.getElementById('message');

function renderUser(text) {
  const div = document.createElement('div');
  div.className = 'user';
  div.innerHTML = `<p>${escapeHtml(text)}</p>`;
  chatEl.appendChild(div);
}

function renderAssistantMessage(text) {
  const div = document.createElement('div');
  div.className = 'assistant';
  div.innerHTML = `<p>${escapeHtml(text)}</p>`;
  chatEl.appendChild(div);
}

function renderRecommendations(payload) {
  const div = document.createElement('div');
  div.className = 'assistant';
  const items = payload.items.map(item => `
    <div class="card">
      <h4>${escapeHtml(item.name)}</h4>
      <div class="price">${item.price}</div>
      <div class="specs">${escapeHtml(item.summary)}</div>
      <div class="proscons">
        <div>
          <strong>Pros</strong>
          <ul>${item.pros.map(p => `<li>${escapeHtml(p)}</li>`).join('')}</ul>
        </div>
        <div>
          <strong>Cons</strong>
          <ul>${item.cons.map(c => `<li>${escapeHtml(c)}</li>`).join('')}</ul>
        </div>
      </div>
    </div>
  `).join('');
  div.innerHTML = `<p>${escapeHtml(payload.rationale)}</p><div class="card-grid">${items}</div>`;
  chatEl.appendChild(div);
}

function renderComparison(payload) {
  const div = document.createElement('div');
  div.className = 'assistant';
  const items = payload.items.map(item => `
    <div class="card">
      <h4>${escapeHtml(item.name)}</h4>
      <div class="price">${item.price}</div>
      <div class="specs">Camera: ${escapeHtml(item.camera)}</div>
      <div class="specs">Battery: ${escapeHtml(item.battery)}</div>
      <div class="specs">Display: ${escapeHtml(item.display)}</div>
      <div class="specs">SoC: ${escapeHtml(item.soc)}</div>
      <div class="proscons">
        <div>
          <strong>Pros</strong>
          <ul>${item.pros.map(p => `<li>${escapeHtml(p)}</li>`).join('')}</ul>
        </div>
        <div>
          <strong>Cons</strong>
          <ul>${item.cons.map(c => `<li>${escapeHtml(c)}</li>`).join('')}</ul>
        </div>
      </div>
    </div>
  `).join('');
  div.innerHTML = `<p>Side-by-side comparison:</p><div class="card-grid">${items}</div>`;
  chatEl.appendChild(div);
}

function renderExplainer(payload) {
  renderAssistantMessage(payload.message);
}

function renderNoResults(payload) {
  renderAssistantMessage(payload.message);
}

function renderRefusal(payload) {
  renderAssistantMessage(payload.message);
}

function escapeHtml(str) {
  return str.replace(/[&<>"]+/g, s => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[s]));
}

async function sendMessage(text) {
  renderUser(text);
  inputEl.value = '';
  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text })
    });
    const data = await res.json();
    if (data.type === 'recommendations') return renderRecommendations(data);
    if (data.type === 'comparison') return renderComparison(data);
    if (data.type === 'explainer') return renderExplainer(data);
    if (data.type === 'no_results') return renderNoResults(data);
    if (data.type === 'refusal') return renderRefusal(data);
    renderAssistantMessage('Sorry, I did not understand that.');
  } catch (e) {
    renderAssistantMessage('Network error. Please try again.');
  } finally {
    chatEl.scrollTop = chatEl.scrollHeight;
  }
}

formEl.addEventListener('submit', (e) => {
  e.preventDefault();
  const text = inputEl.value.trim();
  if (!text) return;
  sendMessage(text);
});


