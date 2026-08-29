/**
 * NetSage AI — Frontend Controller Application
 * Manages view routing, API data fetching, interactive charts,
 * diagnosis execution, mandatory human review workflow, and verification simulator.
 */

// State Management
const state = {
  activeView: 'dashboard',
  cases: [],
  filteredCases: [],
  selectedCase: null,
  activeDiagnosis: null,
  metrics: null,
  responsibleAiLogs: []
};

// API Base URL (relative for single-origin or configured)
const API_BASE = '';

// DOM Elements Initialization
document.addEventListener('DOMContentLoaded', () => {
  initPreloader();
  initNavigation();
  initEventListeners();
  loadInitialData();
});

function initPreloader() {
  const preloader = document.getElementById('app-preloader');
  const bar = document.getElementById('preloader-progress');
  const status = document.getElementById('preloader-status-text');

  if (!preloader || !bar) return;

  // Step 1
  bar.style.width = '35%';
  if (status) status.textContent = 'Loading Cisco Packet Tracer cases...';

  setTimeout(() => {
    bar.style.width = '75%';
    if (status) status.textContent = 'Synchronizing Deterministic Rule Checker...';
  }, 400);

  setTimeout(() => {
    bar.style.width = '100%';
    if (status) status.textContent = 'Ready · NetSage AI Online';
  }, 800);

  setTimeout(() => {
    preloader.classList.add('fade-out');
  }, 1100);
}

function initNavigation() {
  const navItems = document.querySelectorAll('.nav-item');
  navItems.forEach(item => {
    item.addEventListener('click', () => {
      const viewName = item.getAttribute('data-view');
      switchView(viewName);
    });
  });

  const btnViewAll = document.getElementById('btn-view-all-cases');
  if (btnViewAll) {
    btnViewAll.addEventListener('click', () => switchView('explorer'));
  }

  const btnQuickDemo = document.getElementById('btn-quick-diagnose');
  if (btnQuickDemo) {
    btnQuickDemo.addEventListener('click', () => {
      if (state.cases.length > 0) {
        selectCaseForStudio(state.cases[0]);
        switchView('studio');
      }
    });
  }
}

function switchView(viewName) {
  state.activeView = viewName;

  // Update Nav
  document.querySelectorAll('.nav-item').forEach(item => {
    item.classList.toggle('active', item.getAttribute('data-view') === viewName);
  });

  // Update View Panels
  document.querySelectorAll('.view-panel').forEach(panel => {
    panel.classList.toggle('active', panel.id === `view-${viewName}`);
  });

  // Update Topbar Titles
  const titles = {
    dashboard: { tag: '[ 01 / Overview ]', title: 'Executive Dashboard <span class="serif-accent">at a glance.</span>', subtitle: 'Real-time overview of AI diagnosis performance, human oversight, and dataset distribution.' },
    explorer: { tag: '[ 02 / Knowledge Base ]', title: 'Case Explorer <span class="serif-accent">39 lab scenarios.</span>', subtitle: 'Browse Cisco Packet Tracer lab cases with complete topology and show-command evidence.' },
    studio: { tag: '[ 03 / Diagnostics ]', title: 'Diagnosis Studio <span class="serif-accent">& human review gate.</span>', subtitle: 'Deterministic rule validation, AI-assisted root cause analysis, and mandatory human review.' },
    verifier: { tag: '[ 04 / Verification ]', title: 'Packet Tracer Lab Verifier <span class="serif-accent">closed loop.</span>', subtitle: 'Simulate applying configuration fixes and verify resolution in a virtual network environment.' },
    responsible: { tag: '[ 05 / Safety & Audit ]', title: 'Responsible AI & Correction Audit <span class="serif-accent">5 case log.</span>', subtitle: 'Registry of failure modes and human expert corrections ensuring AI safety and reliability.' }
  };

  const current = titles[viewName] || titles.dashboard;
  const tagEl = document.getElementById('page-tag');
  if (tagEl) tagEl.textContent = current.tag;
  document.getElementById('page-title').innerHTML = current.title;
  document.getElementById('page-subtitle').textContent = current.subtitle;

  if (viewName === 'dashboard') {
    fetchMetrics();
  } else if (viewName === 'responsible') {
    fetchResponsibleAiLogs();
  }
}

async function loadInitialData() {
  await fetchMetrics();
  await fetchCases();
  await fetchResponsibleAiLogs();
}

// ---------------- API Calls ----------------

async function fetchMetrics() {
  try {
    const res = await fetch(`${API_BASE}/api/metrics`);
    if (!res.ok) throw new Error('Failed to load metrics');
    const data = await res.json();
    state.metrics = data;
    renderMetrics(data);
  } catch (err) {
    console.error('Error fetching metrics:', err);
  }
}

async function fetchCases() {
  try {
    const res = await fetch(`${API_BASE}/api/cases`);
    if (!res.ok) throw new Error('Failed to load cases');
    const data = await res.json();
    state.cases = data;
    state.filteredCases = data;
    renderExplorerList();
    renderDashboardTable();
    populateVerifierSelect();
  } catch (err) {
    console.error('Error fetching cases:', err);
  }
}

async function fetchResponsibleAiLogs() {
  try {
    const res = await fetch(`${API_BASE}/api/responsible-ai`);
    if (!res.ok) throw new Error('Failed to load responsible AI logs');
    const data = await res.json();
    state.responsibleAiLogs = data;
    renderResponsibleAiTable(data);
  } catch (err) {
    console.error('Error fetching responsible AI logs:', err);
  }
}

// ---------------- Rendering Logic ----------------

function animateValue(element, start, end, duration = 800, suffix = '') {
  if (!element) return;
  const startTime = performance.now();
  
  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    // Smooth ease-out curve
    const ease = 1 - Math.pow(1 - progress, 3);
    const current = Math.floor(start + (end - start) * ease);
    element.textContent = `${current}${suffix}`;
    if (progress < 1) {
      requestAnimationFrame(update);
    } else {
      element.textContent = `${end}${suffix}`;
    }
  }
  requestAnimationFrame(update);
}

function renderMetrics(data) {
  if (!data) return;

  const totalCasesEl = document.getElementById('kpi-total-cases');
  const agreementRateEl = document.getElementById('kpi-agreement-rate');
  const reviewedCasesEl = document.getElementById('kpi-reviewed-cases');
  const responsibleCountEl = document.getElementById('kpi-responsible-count');

  animateValue(totalCasesEl, 0, data.total_cases || 39, 700);

  const totalReviewed = data.reviews?.total_reviewed || 0;
  const agreementRate = data.reviews?.agreement_rate;

  if (totalReviewed === 0 || agreementRate === null || agreementRate === undefined) {
    if (agreementRateEl) agreementRateEl.textContent = 'N/A';
  } else {
    animateValue(agreementRateEl, 0, Math.round(agreementRate), 800, '%');
  }

  animateValue(reviewedCasesEl, 0, totalReviewed, 600);
  animateValue(responsibleCountEl, 0, data.responsible_ai_count || 5, 700);

  // Render Concept Distribution Chart
  const chartContainer = document.getElementById('concept-chart');
  chartContainer.innerHTML = '';
  const total = data.total_cases || 1;

  for (const [concept, count] of Object.entries(data.concept_distribution || {})) {
    const pct = Math.round((count / total) * 100);
    const row = document.createElement('div');
    row.className = 'bar-row';
    row.innerHTML = `
      <span class="bar-label">${concept}</span>
      <div class="bar-track">
        <div class="bar-fill" style="width: ${pct}%"></div>
      </div>
      <span class="bar-val">${count}</span>
    `;
    chartContainer.appendChild(row);
  }

  // Render Review Stats
  const reviewStats = document.getElementById('review-stats');
  reviewStats.innerHTML = `
    <div class="review-stat-box">
      <div>
        <strong>Accepted AI Diagnoses</strong>
        <p class="text-muted">Direct human approval without edits</p>
      </div>
      <span class="badge badge-success" style="font-size: 1rem;">${data.reviews?.accepted || 0}</span>
    </div>
    <div class="review-stat-box">
      <div>
        <strong>Edited Diagnoses (Responsible AI)</strong>
        <p class="text-muted">Human refined or corrected technical details</p>
      </div>
      <span class="badge badge-warning" style="font-size: 1rem;">${data.reviews?.edited || 0}</span>
    </div>
    <div class="review-stat-box">
      <div>
        <strong>Rejected Diagnoses</strong>
        <p class="text-muted">AI output failed validation or evidence mismatch</p>
      </div>
      <span class="badge badge-danger" style="font-size: 1rem;">${data.reviews?.rejected || 0}</span>
    </div>
  `;
}

function renderDashboardTable() {
  const tbody = document.getElementById('dashboard-cases-tbody');
  tbody.innerHTML = '';

  const featured = state.cases.slice(0, 6);
  featured.forEach(c => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong>${c.case_id}</strong></td>
      <td><span class="badge">${c.concept}</span></td>
      <td>${c.osi_layer}</td>
      <td style="max-width: 350px;">${c.symptom}</td>
      <td><span class="badge ${c.severity === 'Critical' ? 'badge-danger' : c.severity === 'High' ? 'badge-warning' : 'badge-primary'}">${c.severity}</span></td>
      <td><button class="btn btn-sm btn-outline btn-table-inspect" data-id="${c.case_id}">Inspect</button></td>
    `;
    tbody.appendChild(tr);
  });

  tbody.querySelectorAll('.btn-table-inspect').forEach(btn => {
    btn.addEventListener('click', () => {
      const caseId = btn.getAttribute('data-id');
      const found = state.cases.find(x => x.case_id === caseId);
      if (found) {
        selectCaseForExplorer(found);
        switchView('explorer');
      }
    });
  });
}

function renderExplorerList() {
  const listContainer = document.getElementById('explorer-cases-list');
  listContainer.innerHTML = '';

  document.getElementById('case-count-label').textContent = `Showing ${state.filteredCases.length} Cases`;

  state.filteredCases.forEach(c => {
    const item = document.createElement('div');
    item.className = `case-item-card ${state.selectedCase?.case_id === c.case_id ? 'active' : ''}`;
    item.innerHTML = `
      <div class="case-item-top">
        <span class="case-item-id">${c.case_id}</span>
        <span class="badge">${c.concept}</span>
      </div>
      <div class="case-item-symptom">${c.symptom}</div>
    `;
    item.addEventListener('click', () => selectCaseForExplorer(c));
    listContainer.appendChild(item);
  });
}

function selectCaseForExplorer(caseItem) {
  state.selectedCase = caseItem;
  renderExplorerList();

  document.getElementById('explorer-empty-state').classList.add('hidden');
  const detail = document.getElementById('explorer-detail-content');
  detail.classList.remove('hidden');

  document.getElementById('detail-case-id').textContent = caseItem.case_id;
  document.getElementById('detail-concept').textContent = caseItem.concept;
  document.getElementById('detail-layer').textContent = caseItem.osi_layer;
  document.getElementById('detail-severity').textContent = caseItem.severity;
  document.getElementById('detail-symptom').textContent = caseItem.symptom;
  document.getElementById('detail-topology').textContent = caseItem.topology_note || 'Direct point-to-point connection';
  document.getElementById('detail-show-output').textContent = caseItem.show_outputs || 'No show command output attached.';
  document.getElementById('detail-expected-fault').textContent = caseItem.expected_fault;
  document.getElementById('detail-expected-fix').textContent = caseItem.expected_fix || 'Configuration update';

  document.getElementById('btn-launch-diagnosis').onclick = () => {
    selectCaseForStudio(caseItem);
    switchView('studio');
  };
}

function selectCaseForStudio(caseItem) {
  state.selectedCase = caseItem;
  document.getElementById('studio-case-badge').textContent = `Case: ${caseItem.case_id}`;
  document.getElementById('studio-input-symptom').value = caseItem.symptom;
  document.getElementById('studio-input-topology').value = caseItem.topology_note || '';
  document.getElementById('studio-input-show').value = caseItem.show_outputs || '';

  // Reset Studio Output
  document.getElementById('studio-root-cause').textContent = "Click 'Execute Diagnosis Pipeline' to generate findings.";
  document.getElementById('studio-evidence-quote').textContent = "Evidence will be quoted from show commands here.";
  document.getElementById('studio-next-cmd').textContent = caseItem.expected_next_command || "show running-config";
  document.getElementById('studio-domain-tag').textContent = `${caseItem.osi_layer} / ${caseItem.concept}`;
  document.getElementById('studio-fix-steps').textContent = caseItem.expected_fix || "Configure corrective commands.";
  document.getElementById('studio-confidence').textContent = "Pending Run";
  document.getElementById('studio-rule-findings').innerHTML = '<div class="empty-finding-note">Run diagnosis to evaluate deterministic rules.</div>';
  document.getElementById('rule-findings-count').textContent = '0 findings';
}

function renderResponsibleAiTable(logs) {
  const tbody = document.getElementById('responsible-ai-tbody');
  if (!tbody) return;
  tbody.innerHTML = '';

  logs.forEach(log => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>
        <span class="badge badge-primary" style="font-size: 0.8rem;">${log.case_id}</span>
      </td>
      <td>
        <span class="badge badge-warning" style="font-size: 0.72rem; line-height: 1.3;">${log.failure_type}</span>
      </td>
      <td style="color: #ef4444; font-size: 0.85rem;">
        <div style="font-weight: 500;">${log.ai_predicted_fault}</div>
      </td>
      <td style="color: #065f46; font-size: 0.85rem; font-weight: 600;">
        <div>${log.human_corrected_fault}</div>
      </td>
      <td style="font-size: 0.82rem; color: var(--color-ink-muted);">
        ${log.why_correction_needed}
      </td>
      <td style="font-size: 0.82rem; color: var(--color-violet-deep); font-style: italic;">
        ${log.lesson_learned}
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function populateVerifierSelect() {
  const select = document.getElementById('verifier-case-select');
  if (!select) return;
  select.innerHTML = '';
  state.cases.forEach(c => {
    const opt = document.createElement('option');
    opt.value = c.case_id;
    opt.textContent = `${c.case_id} — [${c.concept}] ${c.expected_fault.slice(0, 45)}...`;
    select.appendChild(opt);
  });

  if (state.cases.length > 0) {
    updateVerifierCaseDisplay(state.cases[0]);
  }

  select.addEventListener('change', () => {
    const selected = state.cases.find(c => c.case_id === select.value);
    if (selected) updateVerifierCaseDisplay(selected);
  });
}

function updateVerifierCaseDisplay(caseItem) {
  const symptomEl = document.getElementById('verifier-case-symptom');
  if (symptomEl) {
    symptomEl.innerHTML = `
      <strong>Symptom:</strong> ${caseItem.symptom}<br>
      <strong>Expected Fault:</strong> ${caseItem.expected_fault}
    `;
  }
  const fixInput = document.getElementById('verifier-fix-input');
  if (fixInput) {
    fixInput.value = caseItem.expected_fix || '';
  }
  const gateStatusEl = document.getElementById('verifier-gate-status');
  if (gateStatusEl) {
    gateStatusEl.innerHTML = `
      <span class="mono-tag" style="font-size: 0.68rem; color: var(--color-slate);">Target Case: ${caseItem.case_id} · Safety Gate Active</span>
    `;
  }
}

// ---------------- Interactive Event Listeners ----------------

function initEventListeners() {
  // Filter Inputs
  const searchInput = document.getElementById('filter-search');
  const conceptSelect = document.getElementById('filter-concept');
  const layerSelect = document.getElementById('filter-layer');
  const severitySelect = document.getElementById('filter-severity');

  const applyFilters = () => {
    const searchVal = searchInput ? searchInput.value.toLowerCase().trim() : '';
    const conceptVal = conceptSelect ? conceptSelect.value : '';
    const layerVal = layerSelect ? layerSelect.value : '';
    const severityVal = severitySelect ? severitySelect.value : '';

    state.filteredCases = state.cases.filter(c => {
      const matchSearch = !searchVal || 
        c.case_id.toLowerCase().includes(searchVal) ||
        c.symptom.toLowerCase().includes(searchVal) ||
        c.expected_fault.toLowerCase().includes(searchVal) ||
        (c.show_outputs && c.show_outputs.toLowerCase().includes(searchVal));

      const matchConcept = !conceptVal || c.concept === conceptVal;
      const matchLayer = !layerVal || c.osi_layer === layerVal;
      const matchSeverity = !severityVal || c.severity === severityVal;

      return matchSearch && matchConcept && matchLayer && matchSeverity;
    });

    renderExplorerList();
  };

  if (searchInput) searchInput.addEventListener('input', applyFilters);
  if (conceptSelect) conceptSelect.addEventListener('change', applyFilters);
  if (layerSelect) layerSelect.addEventListener('change', applyFilters);
  if (severitySelect) severitySelect.addEventListener('change', applyFilters);

  // Copy Buttons
  const btnCopyNext = document.getElementById('btn-copy-next-cmd');
  if (btnCopyNext) {
    btnCopyNext.addEventListener('click', () => {
      const cmdText = document.getElementById('studio-next-cmd').textContent.replace(/^\$\s*/, '');
      navigator.clipboard.writeText(cmdText).then(() => {
        btnCopyNext.textContent = 'Copied!';
        setTimeout(() => { btnCopyNext.textContent = 'Copy'; }, 1500);
      });
    });
  }

  const btnCopyEvidence = document.getElementById('btn-copy-evidence');
  if (btnCopyEvidence) {
    btnCopyEvidence.addEventListener('click', () => {
      const showText = document.getElementById('studio-input-show').value;
      navigator.clipboard.writeText(showText).then(() => {
        btnCopyEvidence.textContent = 'Copied!';
        setTimeout(() => { btnCopyEvidence.textContent = 'Copy Output'; }, 1500);
      });
    });
  }

  // Diagnosis Execution Button
  const btnRunDiag = document.getElementById('btn-run-diagnosis-engine');
  if (btnRunDiag) {
    btnRunDiag.addEventListener('click', runStudioDiagnosis);
  }

  // Review Actions
  const btnAccept = document.getElementById('btn-review-accept');
  if (btnAccept) {
    btnAccept.addEventListener('click', () => submitReview('ACCEPTED'));
  }

  const btnEdit = document.getElementById('btn-review-edit');
  if (btnEdit) {
    btnEdit.addEventListener('click', () => {
      const editBox = document.getElementById('edit-diagnosis-container');
      editBox.classList.toggle('hidden');
      if (!editBox.classList.contains('hidden')) {
        document.getElementById('edit-diagnosis-input').value = document.getElementById('studio-root-cause').textContent;
        document.getElementById('edit-diagnosis-input').focus();
      }
    });
  }

  const btnReject = document.getElementById('btn-review-reject');
  if (btnReject) {
    btnReject.addEventListener('click', () => submitReview('REJECTED'));
  }

  // Lab Verifier Execution Button
  const btnVerify = document.getElementById('btn-execute-verification');
  if (btnVerify) {
    btnVerify.addEventListener('click', executeVerification);
  }
}

async function runStudioDiagnosis() {
  const symptom = document.getElementById('studio-input-symptom').value.trim();
  const topology = document.getElementById('studio-input-topology').value.trim();
  const showOutputs = document.getElementById('studio-input-show').value.trim();
  const caseId = state.selectedCase ? state.selectedCase.case_id : "CUSTOM";

  if (!symptom || !showOutputs) {
    alert("Please provide symptom and show-command outputs.");
    return;
  }

  const btn = document.getElementById('btn-run-diagnosis-engine');
  btn.disabled = true;
  btn.textContent = "Analyzing Network Evidence...";

  try {
    const res = await fetch(`${API_BASE}/api/diagnose`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symptom, topology_note: topology, show_outputs: showOutputs, case_id: caseId })
    });

    if (!res.ok) throw new Error('Diagnosis pipeline failed');
    const data = await res.json();
    state.activeDiagnosis = data;

    // Render Results
    document.getElementById('studio-root-cause').textContent = data.root_cause;
    document.getElementById('studio-confidence').textContent = `${data.confidence} Confidence`;
    document.getElementById('studio-layer-badge').textContent = data.osi_layer;
    document.getElementById('studio-evidence-quote').textContent = data.evidence;
    document.getElementById('studio-next-cmd').textContent = data.next_command;
    document.getElementById('studio-domain-tag').textContent = `${data.osi_layer} / ${data.concept}`;
    document.getElementById('studio-fix-steps').textContent = data.fix_steps;

    // Render Rule Findings
    const ruleContainer = document.getElementById('studio-rule-findings');
    ruleContainer.innerHTML = '';
    const findings = data.rule_findings || [];
    document.getElementById('rule-findings-count').textContent = `${findings.length} findings`;

    findings.forEach(f => {
      const item = document.createElement('div');
      item.className = `rule-finding-item ${f.status}`;
      item.innerHTML = `
        <strong>[${f.status}] ${f.rule} (${f.severity})</strong><br>
        <span>${f.explanation}</span>
      `;
      ruleContainer.appendChild(item);
    });

    // Reset Review Comments
    document.getElementById('review-comment-input').value = '';
    document.getElementById('edit-diagnosis-container').classList.add('hidden');
    document.getElementById('studio-review-history').innerHTML = '<em>Awaiting human engineer review decision above.</em>';

  } catch (err) {
    console.error('Diagnosis error:', err);
    alert('Failed to execute diagnosis. Check server logs.');
  } finally {
    btn.disabled = false;
    btn.textContent = "Execute Diagnosis Pipeline";
  }
}

async function submitReview(decision) {
  const caseId = state.selectedCase ? state.selectedCase.case_id : "CUSTOM";
  const comment = document.getElementById('review-comment-input').value.trim();
  const editedDiagnosis = document.getElementById('edit-diagnosis-input').value.trim();

  try {
    const res = await fetch(`${API_BASE}/api/review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        case_id: caseId,
        diagnosis_id: state.activeDiagnosis ? state.activeDiagnosis.id : 1,
        decision,
        edited_diagnosis: decision === 'EDITED' ? editedDiagnosis : '',
        reviewer_comment: comment || `Decision marked as ${decision}`
      })
    });

    if (!res.ok) throw new Error('Failed to submit review');
    const data = await res.json();

    const historyBox = document.getElementById('studio-review-history');
    const badgeClass = decision === 'ACCEPTED' ? 'badge-success' : decision === 'EDITED' ? 'badge-warning' : 'badge-danger';
    historyBox.innerHTML = `
      <div style="margin-top: 6px;">
        <span class="badge ${badgeClass}">${decision}</span> by Human Engineer — ${new Date().toLocaleTimeString()}
        <p style="margin-top: 4px; color: #fff;">${comment || 'No comment provided.'}</p>
        ${decision === 'EDITED' ? `<p style="color: #6ee7b7;"><strong>Corrected Diagnosis:</strong> ${editedDiagnosis}</p>` : ''}
      </div>
    `;

    fetchMetrics();
    alert(`Review recorded: ${decision}`);
  } catch (err) {
    console.error('Review error:', err);
    alert('Failed to submit review.');
  }
}

async function executeVerification() {
  const caseSelect = document.getElementById('verifier-case-select');
  const caseId = caseSelect.value;
  const fixCommand = document.getElementById('verifier-fix-input').value.trim();

  const resultBox = document.getElementById('verifier-result-box');
  resultBox.textContent = "Running post-remediation ping and show commands...";

  try {
    const res = await fetch(`${API_BASE}/api/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ case_id: caseId, fix_command: fixCommand })
    });

    if (!res.ok) throw new Error('Verification failed');
    const data = await res.json();

    resultBox.innerHTML = `
      <div style="color: ${data.verified ? '#6ee7b7' : '#fca5a5'}; font-weight: 700; margin-bottom: 6px;">
        STATUS: ${data.status}
      </div>
      <pre style="white-space: pre-wrap; font-family: var(--font-mono);">${data.post_show_outputs}</pre>
    `;
  } catch (err) {
    console.error('Verification error:', err);
    resultBox.textContent = "Error running verification simulator.";
  }
}
