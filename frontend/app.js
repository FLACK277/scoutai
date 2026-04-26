const API = '';  

const SAMPLE_JD = `Senior Backend Engineer — Fintech Startup (Remote)

We are looking for a Senior Backend Engineer to join our growing fintech team. You'll build scalable microservices powering our payment processing platform.

Requirements:
- 4+ years of experience in backend development
- Strong proficiency in Python, FastAPI or Django
- Experience with PostgreSQL and Redis
- Hands-on with Docker and Kubernetes
- Familiarity with AWS or GCP cloud services
- Experience building REST APIs at scale

Nice to have:
- Experience with Kafka or message queues
- CI/CD pipeline experience
- Microservices architecture expertise
- Previous fintech or payments domain experience

Location: Remote (India)`;

let currentResults = null;

document.addEventListener('DOMContentLoaded', () => {
  checkHealth();
});

async function checkHealth() {
  const badge = document.getElementById('modeBadge');
  const text = document.getElementById('modeText');
  const apiDot = document.getElementById('apiDot');
  const apiLabel = document.getElementById('apiLabel');
  const apiDetail = document.getElementById('apiDetail');
  const apiCard = document.getElementById('apiStatusCard');

  try {
    const resp = await fetch(`${API}/health`);
    const data = await resp.json();

    if (data.groq) {
      badge.className = 'mode-badge';
      text.textContent = `Groq Active — ${data.candidates_loaded} candidates`;

      apiCard.className = 'api-status-card active';
      apiDot.className = 'api-dot active';
      apiLabel.textContent = 'Groq API Key Active';
      apiDetail.textContent = `✅ LLM-powered pipeline ready · ${data.candidates_loaded} candidates indexed`;
    } else {
      badge.className = 'mode-badge fallback';
      text.textContent = `Fallback Mode — ${data.candidates_loaded} candidates`;

      apiCard.className = 'api-status-card inactive';
      apiDot.className = 'api-dot inactive';
      apiLabel.textContent = 'Groq API Key Missing';
      apiDetail.textContent = '⚠️ Add GROQ_API_KEY to .env file to enable LLM features';
    }
  } catch (e) {
    badge.className = 'mode-badge fallback';
    text.textContent = 'Server Offline';

    apiCard.className = 'api-status-card offline';
    apiDot.className = 'api-dot offline';
    apiLabel.textContent = 'Server Unreachable';
    apiDetail.textContent = '❌ Cannot connect to backend at localhost:8000';
  }
}
function loadSampleJD() {
  document.getElementById('jdInput').value = SAMPLE_JD;
  document.getElementById('jdInput').focus();
}

function clearAll() {
  document.getElementById('jdInput').value = '';
  document.getElementById('resultsSection').classList.remove('active');
  document.getElementById('parsedJdSection').classList.remove('active');
  document.getElementById('pipelineProgress').classList.remove('active');
  document.getElementById('candidateCards').innerHTML = '';
  currentResults = null;
}
async function runPipeline() {
  const jdText = document.getElementById('jdInput').value.trim();
  if (!jdText) {
    alert('Please enter a job description first.');
    return;
  }

  const anonymize = document.getElementById('anonymizeToggle').checked;
  const btn = document.getElementById('btnRunPipeline');

  // Disable button
  btn.disabled = true;
  btn.innerHTML = '<div class="spinner"></div> Running Pipeline...';

  // Show progress
  showProgress(true);
  updateProgress(1, 'Parsing job description...');

  // Hide old results
  document.getElementById('resultsSection').classList.remove('active');
  document.getElementById('parsedJdSection').classList.remove('active');

  try {
    // Simulate step progress while waiting for the single pipeline call
    const progressPromise = animateProgress();

    const resp = await fetch(`${API}/pipeline`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ jd_text: jdText, top_k: 10, anonymize }),
    });

    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.detail || 'Pipeline failed');
    }

    const data = await resp.json();
    currentResults = data;

    // Complete progress
    updateProgress(6, 'Done!');
    await sleep(400);
    showProgress(false);

    // Render results
    renderParsedJD(data.jd_parsed);
    renderResults(data);

    // Refresh health
    checkHealth();

  } catch (err) {
    showProgress(false);
    alert(`Pipeline Error: ${err.message}`);
    console.error(err);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '🚀 Run Full Pipeline';
  }
}

// ─── Progress Animation ──────────────────────────────────────────────────────
function showProgress(visible) {
  const el = document.getElementById('pipelineProgress');
  el.classList.toggle('active', visible);
  if (!visible) {
    document.querySelectorAll('.progress-step').forEach(s => {
      s.className = 'progress-step';
    });
  }
}

function updateProgress(step, text) {
  document.getElementById('progressText').textContent = text;
  const steps = document.querySelectorAll('.progress-step');
  steps.forEach((s, i) => {
    const n = i + 1;
    if (n < step) s.className = 'progress-step done';
    else if (n === step) s.className = 'progress-step active';
    else s.className = 'progress-step';
  });
}

async function animateProgress() {
  const labels = [
    [1, 'Parsing job description...'],
    [2, 'Retrieving candidates via Hybrid RAG...'],
    [3, 'Scoring candidates...'],
    [4, 'Computing propensity-to-switch...'],
    [5, 'Generating explanations & outreach...'],
    [6, 'Computing final rankings...'],
  ];
  for (const [step, label] of labels) {
    updateProgress(step, label);
    await sleep(800);
  }
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// ─── Render Parsed JD ────────────────────────────────────────────────────────
function renderParsedJD(jd) {
  const section = document.getElementById('parsedJdSection');
  const content = document.getElementById('parsedJdContent');

  let html = `
    <div style="margin-bottom: 12px;">
      <span style="color: var(--text-muted); font-size: 0.78rem;">Role:</span>
      <span style="font-weight: 600; margin-left: 6px;">${esc(jd.role)}</span>
    </div>
    <div style="margin-bottom: 12px;">
      <span style="color: var(--text-muted); font-size: 0.78rem;">Experience:</span>
      <span style="font-weight: 600; margin-left: 6px;">${jd.experience_required}+ years</span>
      <span style="color: var(--text-muted); margin-left: 16px; font-size: 0.78rem;">Location:</span>
      <span style="font-weight: 600; margin-left: 6px;">${esc(jd.location)}</span>
    </div>
    <div style="margin-bottom: 8px;">
      <span style="color: var(--text-muted); font-size: 0.78rem;">Must-have Skills:</span>
      <div class="jd-chips">
        ${jd.skills_must_have.map(s => `<span class="skill-tag matched">${esc(s)}</span>`).join('')}
      </div>
    </div>`;

  if (jd.skills_nice_to_have && jd.skills_nice_to_have.length > 0) {
    html += `
    <div>
      <span style="color: var(--text-muted); font-size: 0.78rem;">Nice-to-have:</span>
      <div class="jd-chips">
        ${jd.skills_nice_to_have.map(s => `<span class="skill-tag neutral">${esc(s)}</span>`).join('')}
      </div>
    </div>`;
  }

  content.innerHTML = html;
  section.classList.add('active');
}

// ─── Render Results ──────────────────────────────────────────────────────────
function renderResults(data) {
  const section = document.getElementById('resultsSection');
  const meta = document.getElementById('resultsMeta');
  const cards = document.getElementById('candidateCards');

  // Meta chips
  meta.innerHTML = `
    <span class="meta-chip">⏱ ${data.elapsed_seconds}s</span>
    <span class="meta-chip">👥 ${data.total_candidates} total</span>
    <span class="meta-chip">🎯 ${data.shortlisted} shortlisted</span>
    <span class="meta-chip">${data.mode === 'llm' ? '🟢 Groq' : '🟡 Fallback'}</span>
  `;

  // Candidate cards
  cards.innerHTML = data.ranked.map(c => renderCandidateCard(c)).join('');
  section.classList.add('active');
}

function renderCandidateCard(c) {
  const rankClass = c.rank <= 3 ? `rank-${c.rank}` : 'rank-default';
  const scoreClass = c.final_score >= 65 ? 'score-high' : c.final_score >= 45 ? 'score-mid' : 'score-low';

  const interestClass = c.interest_level === 'Interested' ? 'interested'
    : c.interest_level === 'Not Interested' ? 'not-interested' : 'neutral';

  return `
  <div class="candidate-card" id="card-${c.candidate_id}">
    <div class="card-main" onclick="toggleCard(${c.candidate_id})">
      <div class="rank-badge ${rankClass}">#${c.rank}</div>
      <div class="card-info">
        <div class="card-name">${esc(c.name)}</div>
        <div class="card-company">${esc(c.current_company)} · ${c.experience_years} yrs · 
          <span class="interest-badge ${interestClass}">${esc(c.interest_level)}</span>
        </div>
      </div>
      <div class="card-scores">
        <div class="score-ring">
          <div class="score-ring-value ${scoreClass}">${Math.round(c.final_score)}</div>
          <div class="score-ring-label">Final</div>
        </div>
        <span class="expand-icon">▾</span>
      </div>
    </div>
    <div class="card-details">
      <div class="details-grid">
        <!-- Score Breakdown -->
        <div class="detail-block">
          <div class="detail-block-title">Score Breakdown</div>
          <div class="score-bars">
            ${scoreBar('Match', c.match_score, 'indigo')}
            ${scoreBar('Skill', c.skill_score, 'emerald')}
            ${scoreBar('Experience', c.experience_score, 'cyan')}
            ${scoreBar('Semantic', c.semantic_score, 'amber')}
            ${scoreBar('Propensity', c.propensity_score, 'rose')}
            ${scoreBar('Interest', c.interest_score, 'indigo')}
          </div>
        </div>

        <!-- Skills -->
        <div class="detail-block">
          <div class="detail-block-title">Skills Analysis</div>
          <div class="skill-tags" style="margin-bottom: 10px;">
            ${(c.matched_skills || []).map(s => `<span class="skill-tag matched">✓ ${esc(s)}</span>`).join('')}
            ${(c.missing_skills || []).map(s => `<span class="skill-tag missing">✗ ${esc(s)}</span>`).join('')}
          </div>
          <div style="margin-top: 8px; font-size: 0.78rem; color: var(--text-muted);">
            ${esc(c.propensity_reason)}
          </div>
        </div>

        <!-- Explanation -->
        <div class="detail-block">
          <div class="detail-block-title">AI Explanation</div>
          <p class="explanation-summary">${esc(c.explanation_summary)}</p>
          ${(c.strengths && c.strengths.length) ? `
          <div style="margin-top: 10px;">
            <div style="font-size: 0.72rem; color: var(--text-muted); margin-bottom: 4px;">Strengths:</div>
            <ul class="evidence-list">
              ${c.strengths.map(s => `<li>${esc(s)}</li>`).join('')}
            </ul>
          </div>` : ''}
          ${(c.resume_evidence && c.resume_evidence.length) ? `
          <div style="margin-top: 10px;">
            <div style="font-size: 0.72rem; color: var(--text-muted); margin-bottom: 4px;">Resume Evidence:</div>
            <ul class="evidence-list">
              ${c.resume_evidence.map(e => `<li>${esc(e)}</li>`).join('')}
            </ul>
          </div>` : ''}
        </div>

        <!-- Engagement -->
        <div class="detail-block">
          <div class="detail-block-title">Outreach & Response</div>
          ${c.outreach_message ? `
            <div style="font-size: 0.72rem; color: var(--text-muted); margin-bottom: 4px;">📤 Outreach Message:</div>
            <div class="outreach-message">${esc(c.outreach_message)}</div>
          ` : ''}
          ${c.candidate_response ? `
            <div style="font-size: 0.72rem; color: var(--text-muted); margin-bottom: 4px;">💬 Simulated Response:</div>
            <div class="candidate-response-text">${esc(c.candidate_response)}</div>
          ` : ''}
        </div>
      </div>
      <div style="text-align: center; margin-top: 14px;">
        <span style="font-size: 0.68rem; color: var(--text-muted);">${esc(c.bias_note)}</span>
      </div>
    </div>
  </div>`;
}

function scoreBar(label, value, color) {
  const v = Math.round(value || 0);
  return `
    <div class="score-bar-row">
      <span class="score-bar-label">${label}</span>
      <div class="score-bar-track">
        <div class="score-bar-fill ${color}" style="width: ${v}%"></div>
      </div>
      <span class="score-bar-value">${v}</span>
    </div>`;
}

// ─── Toggle Card ─────────────────────────────────────────────────────────────
function toggleCard(id) {
  const card = document.getElementById(`card-${id}`);
  if (card) card.classList.toggle('expanded');
}

// ─── Escape HTML ─────────────────────────────────────────────────────────────
function esc(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = String(str);
  return div.innerHTML;
}
