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

  // Auto-close mobile drawer if open
  const sidebar = document.querySelector('.sidebar');
  const backdrop = document.getElementById('sidebar-backdrop');
  if (sidebar) sidebar.classList.remove('mobile-open');
  if (backdrop) backdrop.classList.remove('active');

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
  } else if (viewName === 'studio') {
    if (state.cases && state.cases.length > 0) {
      selectCaseForStudio(state.selectedCase || state.cases[0]);
    }
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
    populateStudioCaseSelect();

    // Default select first case in Studio if none active
    if (!state.selectedCase && data.length > 0) {
      selectCaseForStudio(data[0]);
    }
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

  // 1. Studio Header Card
  const titleEl = document.getElementById('studio-active-case-title');
  if (titleEl) titleEl.textContent = `${caseItem.case_id} — ${caseItem.expected_fault}`;

  const caseBadge = document.getElementById('studio-case-id-badge');
  if (caseBadge) caseBadge.textContent = caseItem.case_id;

  const conceptBadge = document.getElementById('studio-concept-badge');
  if (conceptBadge) conceptBadge.textContent = caseItem.concept;

  const sevBadge = document.getElementById('studio-severity-badge');
  if (sevBadge) {
    sevBadge.textContent = (caseItem.severity || 'HIGH').toUpperCase();
    sevBadge.className = `badge ${caseItem.severity === 'Critical' ? 'badge-danger' : 'badge-warning'}`;
  }

  const layerBadgeHdr = document.getElementById('studio-layer-badge-header');
  if (layerBadgeHdr) layerBadgeHdr.textContent = caseItem.osi_layer || 'Layer 2';

  const statusPill = document.getElementById('studio-status-pill');
  if (statusPill) {
    statusPill.textContent = 'Awaiting Investigation';
    statusPill.className = 'studio-status-pill pending';
  }

  // Sync Studio quick case select
  const quickSelect = document.getElementById('studio-quick-case-select');
  if (quickSelect && quickSelect.value !== caseItem.case_id) {
    quickSelect.value = caseItem.case_id;
  }

  // 2. Incident Card
  const incSymptom = document.getElementById('studio-incident-symptom');
  if (incSymptom) incSymptom.textContent = caseItem.symptom;

  const incSev = document.getElementById('studio-incident-severity');
  if (incSev) incSev.textContent = `${(caseItem.severity || 'HIGH').toUpperCase()} SEVERITY`;

  const metaCaseId = document.getElementById('meta-case-id');
  if (metaCaseId) metaCaseId.textContent = caseItem.case_id;

  const metaDomain = document.getElementById('meta-domain');
  if (metaDomain) metaDomain.textContent = `${caseItem.concept} / Networking`;

  const metaLayer = document.getElementById('meta-layer');
  if (metaLayer) metaLayer.textContent = caseItem.osi_layer;

  // 3. Topology Section
  const topoDisplay = document.getElementById('studio-topology-display');
  if (topoDisplay) topoDisplay.textContent = caseItem.topology_note || 'Direct interconnect topology';

  // 4. Cisco IOS Terminal Evidence Viewer
  const termTitle = document.getElementById('terminal-device-title');
  if (termTitle) termTitle.textContent = `Cisco IOS v15.4 · Device Console (${caseItem.case_id})`;

  const termBody = document.getElementById('studio-terminal-body');
  if (termBody) termBody.textContent = caseItem.show_outputs || '# No show command captures attached.';

  // 5. Reset Pipeline Steps
  resetPipelineTracker();

  // 6. Reset Deterministic Rule Findings
  const ruleFindings = document.getElementById('studio-rule-findings');
  if (ruleFindings) {
    ruleFindings.innerHTML = '<div class="empty-finding-note">Click "Execute Complete Diagnosis Pipeline" to evaluate deterministic network rules.</div>';
  }
  const findingsCount = document.getElementById('rule-findings-count');
  if (findingsCount) findingsCount.textContent = '6 Checks Armed';

  resetDeterministicChips();

  // 7. Reset AI Diagnosis Card
  const rootCauseEl = document.getElementById('studio-root-cause');
  if (rootCauseEl) rootCauseEl.textContent = "Run diagnosis to generate evidence-backed root cause analysis.";

  const confScoreEl = document.getElementById('studio-confidence-score');
  if (confScoreEl) confScoreEl.textContent = "--%";

  const confFillEl = document.getElementById('studio-confidence-fill');
  if (confFillEl) confFillEl.style.width = "0%";

  const confLevelEl = document.getElementById('studio-confidence');
  if (confLevelEl) {
    confLevelEl.textContent = "Pending Execution";
    confLevelEl.style.color = "var(--color-slate)";
  }

  const layerBadge = document.getElementById('studio-layer-badge');
  if (layerBadge) layerBadge.textContent = `${caseItem.osi_layer} · ${caseItem.concept}`;

  const quoteEl = document.getElementById('studio-evidence-quote');
  if (quoteEl) quoteEl.textContent = "Exact matching evidence quotations from show commands will be extracted here.";

  const whyMattersEl = document.getElementById('studio-why-matters');
  if (whyMattersEl) whyMattersEl.innerHTML = `<strong>Why this matters:</strong> Observations from show-command captures corroborate root cause at ${caseItem.osi_layer}.`;

  const nextCmdEl = document.getElementById('studio-next-cmd');
  if (nextCmdEl) nextCmdEl.textContent = `$ ${caseItem.expected_next_command || "show running-config"}`;

  const nextCmdPurpose = document.getElementById('studio-cmd-purpose');
  if (nextCmdPurpose) nextCmdPurpose.textContent = `Purpose: Verify active ${caseItem.concept} configuration and telemetry on device.`;

  // Numbered Fix Steps
  renderFixSteps(caseItem.expected_fix || "Configure corrective commands on Cisco device.");

  // 8. Mandatory Human Review Reset
  const gatePill = document.getElementById('gate-status-pill');
  if (gatePill) {
    gatePill.textContent = 'AWAITING HUMAN APPROVAL';
    gatePill.className = 'badge badge-warning';
  }

  const linkageEl = document.getElementById('studio-verification-linkage');
  if (linkageEl) {
    linkageEl.innerHTML = `
      <span class="badge badge-warning">AWAITING HUMAN APPROVAL</span>
      <span class="linkage-text">Automated verification is locked until signed off above.</span>
    `;
  }

  const editContainer = document.getElementById('edit-diagnosis-container');
  if (editContainer) editContainer.classList.add('hidden');

  const commentInput = document.getElementById('review-comment-input');
  if (commentInput) commentInput.value = '';
}

function resetPipelineTracker() {
  for (let i = 1; i <= 6; i++) {
    const step = document.getElementById(`pipe-step-${i}`);
    if (step) {
      step.classList.remove('active', 'completed');
    }
  }
  const statusText = document.getElementById('pipeline-status-text');
  if (statusText) statusText.textContent = 'Standby · Ready to Execute';
}

function resetDeterministicChips() {
  ['chip-interface', 'chip-vlan', 'chip-ip', 'chip-routing'].forEach(id => {
    const chip = document.getElementById(id);
    if (chip) {
      chip.className = 'chip-item';
      if (id === 'chip-interface') chip.textContent = '✓ Interface Status';
      if (id === 'chip-vlan') chip.textContent = '✓ VLAN Config';
      if (id === 'chip-ip') chip.textContent = '✓ IP Addressing';
      if (id === 'chip-routing') chip.textContent = '✓ Routing Protocol';
    }
  });
}

function renderFixSteps(fixText) {
  const container = document.getElementById('studio-fix-steps');
  if (!container) return;
  container.innerHTML = '';

  const steps = fixText.split(/[;\n]/).map(s => s.trim()).filter(s => s.length > 0);
  if (steps.length === 0) steps.push(fixText);

  steps.forEach((step, idx) => {
    const item = document.createElement('div');
    item.className = 'fix-step-item';
    const num = (idx + 1).toString().padStart(2, '0');
    item.innerHTML = `
      <span class="step-index">${num}</span>
      <span class="step-text">${step}</span>
    `;
    container.appendChild(item);
  });
}

function populateStudioCaseSelect() {
  const select = document.getElementById('studio-quick-case-select');
  if (!select) return;
  select.innerHTML = '';

  state.cases.forEach(c => {
    const opt = document.createElement('option');
    opt.value = c.case_id;
    opt.textContent = `${c.case_id} — [${c.concept}] ${c.expected_fault.slice(0, 38)}...`;
    select.appendChild(opt);
  });

  select.addEventListener('change', () => {
    const selected = state.cases.find(c => c.case_id === select.value);
    if (selected) {
      selectCaseForStudio(selected);
    }
  });
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
      const showText = document.getElementById('studio-terminal-body').textContent;
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

  // Mobile Drawer Navigation Toggle
  const mobileBtn = document.getElementById('mobile-menu-btn');
  const sidebar = document.querySelector('.sidebar');
  const backdrop = document.getElementById('sidebar-backdrop');
  if (mobileBtn && sidebar) {
    mobileBtn.addEventListener('click', () => {
      sidebar.classList.toggle('mobile-open');
      if (backdrop) backdrop.classList.toggle('active');
    });
  }
  if (backdrop) {
    backdrop.addEventListener('click', () => {
      sidebar.classList.remove('mobile-open');
      backdrop.classList.remove('active');
    });
  }

  // System Diagnostics & Health Telemetry Modal
  const btnSystemStatus = document.getElementById('btn-system-status');
  const modal = document.getElementById('system-health-modal');
  const btnCloseModal = document.getElementById('btn-close-modal');
  const btnPingHealth = document.getElementById('btn-ping-health');

  if (btnSystemStatus && modal) {
    btnSystemStatus.addEventListener('click', () => {
      modal.classList.remove('hidden');
      pingHealthEndpoint();
    });
  }
  if (btnCloseModal && modal) {
    btnCloseModal.addEventListener('click', () => modal.classList.add('hidden'));
  }
  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) modal.classList.add('hidden');
    });
  }
  if (btnPingHealth) {
    btnPingHealth.addEventListener('click', pingHealthEndpoint);
  }

  // Human Override Form Submission
  const btnSubmitOverride = document.getElementById('btn-submit-override');
  if (btnSubmitOverride) {
    btnSubmitOverride.addEventListener('click', () => submitReview('EDITED'));
  }
}

async function pingHealthEndpoint() {
  const pingVal = document.getElementById('health-ping-val');
  if (!pingVal) return;
  pingVal.textContent = 'Pinging...';
  const start = performance.now();
  try {
    const res = await fetch(`${API_BASE}/api/metrics`);
    const duration = Math.round(performance.now() - start);
    if (res.ok) {
      pingVal.textContent = `${duration} ms · 100% HEALTHY`;
      pingVal.style.color = '#059669';
    } else {
      pingVal.textContent = `${duration} ms · WARNING`;
      pingVal.style.color = '#d97706';
    }
  } catch (err) {
    pingVal.textContent = 'OFFLINE';
    pingVal.style.color = '#ef4444';
  }
}

async function runStudioDiagnosis() {
  const caseItem = state.selectedCase;
  const symptom = caseItem ? caseItem.symptom : (document.getElementById('studio-incident-symptom')?.textContent.trim() || '');
  const topology = caseItem ? (caseItem.topology_note || '') : (document.getElementById('studio-topology-display')?.textContent.trim() || '');
  const showOutputs = caseItem ? caseItem.show_outputs : (document.getElementById('studio-terminal-body')?.textContent.trim() || '');
  const caseId = caseItem ? caseItem.case_id : "CUSTOM";

  if (!symptom || !showOutputs) {
    alert("Please select a troubleshooting case or provide show-command outputs.");
    return;
  }

  const btn = document.getElementById('btn-run-diagnosis-engine');
  btn.disabled = true;
  btn.textContent = "Analyzing Network Evidence...";

  // 1. Start Investigation Pipeline Animation
  const statusPill = document.getElementById('studio-status-pill');
  if (statusPill) {
    statusPill.textContent = 'Investigation In Progress';
    statusPill.className = 'studio-status-pill running';
  }

  const pipelineStatus = document.getElementById('pipeline-status-text');
  if (pipelineStatus) pipelineStatus.textContent = 'Evaluating Deterministic Rules & LLM Pipeline...';

  // Animate Pipeline Steps
  document.getElementById('pipe-step-1').className = 'pipeline-step-item completed';
  document.getElementById('pipe-step-2').className = 'pipeline-step-item active';

  try {
    const res = await fetch(`${API_BASE}/api/diagnose`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symptom, topology_note: topology, show_outputs: showOutputs, case_id: caseId })
    });

    if (!res.ok) throw new Error('Diagnosis pipeline failed');
    const data = await res.json();
    state.activeDiagnosis = data;

    // Complete Pipeline Steps
    document.getElementById('pipe-step-2').className = 'pipeline-step-item completed';
    document.getElementById('pipe-step-3').className = 'pipeline-step-item completed';
    document.getElementById('pipe-step-4').className = 'pipeline-step-item completed';
    document.getElementById('pipe-step-5').className = 'pipeline-step-item completed';
    document.getElementById('pipe-step-6').className = 'pipeline-step-item active';

    if (pipelineStatus) pipelineStatus.textContent = 'Investigation Complete · Awaiting Human Safety Sign-Off';

    if (statusPill) {
      statusPill.textContent = 'Diagnosed · Awaiting Review';
      statusPill.className = 'studio-status-pill pending';
    }

    // 1. Render AI Root Cause
    document.getElementById('studio-root-cause').textContent = data.root_cause;

    // 2. Render Confidence Score & Gauge
    let confNum = 88;
    if (typeof data.confidence === 'string') {
      if (data.confidence.toLowerCase().includes('high')) confNum = 88;
      else if (data.confidence.toLowerCase().includes('medium')) confNum = 68;
      else if (data.confidence.toLowerCase().includes('low')) confNum = 42;
      else {
        const parsed = parseInt(data.confidence, 10);
        if (!isNaN(parsed)) confNum = parsed;
      }
    } else if (typeof data.confidence === 'number') {
      confNum = Math.round(data.confidence);
    }

    const confScoreEl = document.getElementById('studio-confidence-score');
    if (confScoreEl) confScoreEl.textContent = `${confNum}%`;

    const confFillEl = document.getElementById('studio-confidence-fill');
    if (confFillEl) confFillEl.style.width = `${confNum}%`;

    const confLevelEl = document.getElementById('studio-confidence');
    if (confLevelEl) {
      confLevelEl.textContent = `${data.confidence.toUpperCase()} CONFIDENCE`;
      confLevelEl.style.color = confNum >= 75 ? '#059669' : confNum >= 50 ? '#d97706' : '#ef4444';
    }

    // 3. Render Badges & Evidence
    document.getElementById('studio-layer-badge').textContent = `${data.osi_layer} · ${data.concept}`;
    document.getElementById('studio-evidence-quote').textContent = data.evidence;
    document.getElementById('studio-why-matters').innerHTML = `<strong>Why this matters:</strong> Evidence from show commands directly confirms ${data.root_cause} at ${data.osi_layer}.`;
    document.getElementById('studio-next-cmd').textContent = data.next_command.startsWith('$') ? data.next_command : `$ ${data.next_command}`;
    document.getElementById('studio-cmd-purpose').textContent = `Purpose: Verify active ${data.concept} configuration and telemetry on device.`;

    // 4. Render Fix Steps as Numbered Cards
    renderFixSteps(data.fix_steps);

    // 5. Render Deterministic Rule Findings
    const ruleContainer = document.getElementById('studio-rule-findings');
    ruleContainer.innerHTML = '';
    const findings = data.rule_findings || [];
    document.getElementById('rule-findings-count').textContent = `${findings.length} Finding${findings.length === 1 ? '' : 's'}`;

    let hasFail = false;
    let hasWarn = false;

    findings.forEach(f => {
      if (f.status === 'FAIL') hasFail = true;
      if (f.status === 'WARNING') hasWarn = true;

      const item = document.createElement('div');
      item.className = `rule-finding-item ${f.status}`;
      item.innerHTML = `
        <strong>[${f.status}] ${f.rule} (${f.severity})</strong><br>
        <span style="font-size: 0.8rem; color: var(--color-ink);">${f.explanation}</span>
      `;
      ruleContainer.appendChild(item);
    });

    if (findings.length === 0) {
      ruleContainer.innerHTML = '<div class="empty-finding-note" style="color: #059669;">✓ All 6 deterministic checks passed with no syntax or containment violations.</div>';
    }

    // Update Summary Chips
    const chipVlan = document.getElementById('chip-vlan');
    if (chipVlan) {
      if (data.concept === 'VLAN' && hasFail) {
        chipVlan.className = 'chip-item fail';
        chipVlan.textContent = '✕ VLAN Violation';
      } else {
        chipVlan.className = 'chip-item pass';
        chipVlan.textContent = '✓ VLAN Verified';
      }
    }

    const chipIp = document.getElementById('chip-ip');
    if (chipIp) {
      if ((data.concept === 'DHCP' || data.concept === 'Routing' || data.concept === 'Gateway') && hasFail) {
        chipIp.className = 'chip-item fail';
        chipIp.textContent = '✕ IP/Subnet Fault';
      } else {
        chipIp.className = 'chip-item pass';
        chipIp.textContent = '✓ IP Addr Valid';
      }
    }

    // Pre-populate Human Override text
    const editAiOriginal = document.getElementById('edit-original-ai-text');
    if (editAiOriginal) editAiOriginal.textContent = data.root_cause;

    const editInput = document.getElementById('edit-diagnosis-input');
    if (editInput) editInput.value = data.root_cause;

    // Reset Review Comments
    document.getElementById('review-comment-input').value = '';
    document.getElementById('edit-diagnosis-container').classList.add('hidden');
    
    // Safety Gate State
    const gatePill = document.getElementById('gate-status-pill');
    if (gatePill) {
      gatePill.textContent = 'AWAITING HUMAN APPROVAL';
      gatePill.className = 'badge badge-warning';
    }

    const linkageEl = document.getElementById('studio-verification-linkage');
    if (linkageEl) {
      linkageEl.innerHTML = `
        <span class="badge badge-warning">AWAITING HUMAN APPROVAL</span>
        <span class="linkage-text">Automated verification is locked until signed off above.</span>
      `;
    }

  } catch (err) {
    console.error('Diagnosis error:', err);
    alert('Failed to execute diagnosis. Check server logs.');
  } finally {
    btn.disabled = false;
    btn.textContent = "Execute Complete Diagnosis Pipeline";
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

    const statusPill = document.getElementById('studio-status-pill');
    const gatePill = document.getElementById('gate-status-pill');
    const linkageEl = document.getElementById('studio-verification-linkage');
    const pipeStep6 = document.getElementById('pipe-step-6');

    if (decision === 'ACCEPTED') {
      if (pipeStep6) pipeStep6.className = 'pipeline-step-item completed';
      if (statusPill) {
        statusPill.textContent = 'Human Approved';
        statusPill.className = 'studio-status-pill approved';
      }
      if (gatePill) {
        gatePill.textContent = 'HUMAN APPROVED';
        gatePill.className = 'badge badge-success';
      }
      if (linkageEl) {
        linkageEl.innerHTML = `
          <span class="badge badge-success">HUMAN APPROVED</span>
          <span class="linkage-text">Safety interlock unlocked · Fix verified for network application.</span>
          <button class="btn btn-sm btn-outline" id="btn-jump-verifier" style="margin-left: auto; padding: 4px 10px; font-size: 0.75rem;">Open in Lab Verifier →</button>
        `;
        document.getElementById('btn-jump-verifier').addEventListener('click', () => switchView('verifier'));
      }
    } else if (decision === 'EDITED') {
      if (pipeStep6) pipeStep6.className = 'pipeline-step-item completed';
      if (statusPill) {
        statusPill.textContent = 'Human Override';
        statusPill.className = 'studio-status-pill edited';
      }
      if (gatePill) {
        gatePill.textContent = 'HUMAN OVERRIDE';
        gatePill.className = 'badge badge-primary';
      }
      if (linkageEl) {
        linkageEl.innerHTML = `
          <span class="badge badge-primary">HUMAN OVERRIDE</span>
          <span class="linkage-text">Human override signed off · Corrective commands logged.</span>
          <button class="btn btn-sm btn-outline" id="btn-jump-verifier" style="margin-left: auto; padding: 4px 10px; font-size: 0.75rem;">Open in Lab Verifier →</button>
        `;
        document.getElementById('btn-jump-verifier').addEventListener('click', () => switchView('verifier'));
      }
      document.getElementById('edit-diagnosis-container').classList.add('hidden');
    } else if (decision === 'REJECTED') {
      if (statusPill) {
        statusPill.textContent = 'Rejected';
        statusPill.className = 'studio-status-pill rejected';
      }
      if (gatePill) {
        gatePill.textContent = 'REJECTED';
        gatePill.className = 'badge badge-danger';
      }
      if (linkageEl) {
        linkageEl.innerHTML = `
          <span class="badge badge-danger">REJECTED</span>
          <span class="linkage-text">Automated remediation blocked by human engineer.</span>
        `;
      }
    }

    fetchMetrics();
    alert(`Human review recorded: ${decision}`);
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
