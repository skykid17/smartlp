const panels = Array.from(document.querySelectorAll('[data-step-panel]'));
const stepIndicator = document.getElementById('stepIndicator');
const alertBox = document.getElementById('alert');
const successBox = document.getElementById('success');
const statusBadge = document.getElementById('statusBadge');

const state = {
  step: 1,
  siem: { tested: false },
  llm: { tested: false },
};

function setAlert(message) {
  // Alerts are mutually exclusive
  setSuccess('');
  if (!message) {
    alertBox.classList.add('hidden');
    alertBox.textContent = '';
    return;
  }
  alertBox.textContent = message;
  alertBox.classList.remove('hidden');
}

function setSuccess(message) {
  // Alerts are mutually exclusive
  if (message) setAlert('');
  if (!message) {
    successBox.classList.add('hidden');
    successBox.textContent = '';
    return;
  }
  successBox.textContent = message;
  successBox.classList.remove('hidden');
}

function setStep(step) {
  state.step = step;
  setAlert('');
  setSuccess('');

  panels.forEach((p) => {
    p.classList.toggle('hidden', p.getAttribute('data-step-panel') !== String(step));
  });

  Array.from(stepIndicator.querySelectorAll('[data-step]')).forEach((el) => {
    el.classList.toggle('font-medium', el.getAttribute('data-step') === String(step));
    el.classList.toggle('text-gray-900', el.getAttribute('data-step') === String(step));
    el.classList.toggle('text-gray-600', el.getAttribute('data-step') !== String(step));
  });
}

function jsonOrThrow(resp) {
  return resp
    .json()
    .catch(() => ({}))
    .then((body) => {
      if (!resp.ok) {
        const msg = body.error || body.message || 'Request failed';
        throw new Error(msg);
      }
      return body;
    });
}

function getSiemPayload() {
  const siem = document.getElementById('siemType').value;
  if (siem === 'elastic') {
    return {
      siem,
      host: document.getElementById('elasticHost').value,
      api_key: document.getElementById('elasticApiKey').value,
      kibana_url: document.getElementById('elasticKibanaUrl').value,
      user: document.getElementById('elasticUser').value,
      password: document.getElementById('elasticPassword').value,
      search_index: document.getElementById('elasticSearchIndex').value,
      search_query: document.getElementById('elasticSearchQuery') ? document.getElementById('elasticSearchQuery').value : '',
      cert_path: document.getElementById('elasticCertPath').value,
    };
  }

  if (siem === 'splunk') {
    return {
      siem,
      host: document.getElementById('splunkHost').value,
      port: document.getElementById('splunkPort').value,
      user: document.getElementById('splunkUser').value,
      password: document.getElementById('splunkPassword').value,
      search_index: document.getElementById('splunkSearchIndex').value,
      search_query: document.getElementById('splunkSearchQuery').value,
      search_entry_count: document.getElementById('splunkSearchEntryCount').value,
    };
  }

  return { siem };
}

function getLlmPayload() {
  return {
    provider: document.getElementById('llmProvider').value,
    endpoint_url: document.getElementById('llmEndpointUrl').value,
    api_key: document.getElementById('llmApiKey').value,
    model_name: document.getElementById('llmModelName').value,
  };
}

function updateReview() {
  const siem = document.getElementById('siemType').value;
  const llmProvider = document.getElementById('llmProvider').value;
  const llmModel = document.getElementById('llmModelName').value;
  const llmUrl = document.getElementById('llmEndpointUrl').value;

  document.getElementById('reviewSiem').textContent = siem ? siem.toUpperCase() : '—';
  document.getElementById('reviewLlm').textContent =
    llmProvider && llmModel ? `${llmProvider.toUpperCase()} — ${llmModel} @ ${llmUrl}` : '—';
}

// SIEM selector UI
const siemType = document.getElementById('siemType');
const elasticFields = document.getElementById('elasticFields');
const splunkFields = document.getElementById('splunkFields');

siemType.addEventListener('change', () => {
  const v = siemType.value;
  elasticFields.classList.toggle('hidden', v !== 'elastic');
  splunkFields.classList.toggle('hidden', v !== 'splunk');
  state.siem.tested = false;
  document.getElementById('btnSiemNext').disabled = true;
});

// Step 1 buttons
document.getElementById('btnSiemTest').addEventListener('click', async () => {
  setAlert('');
  setSuccess('');
  const siemSpinner = document.getElementById('siemSpinner');
  const siemBtn = document.getElementById('btnSiemTest');
  if (siemSpinner) siemSpinner.classList.remove('hidden');
  if (siemBtn) siemBtn.disabled = true;

  try {
    const body = getSiemPayload();
    const resp = await fetch('/api/init/siem/test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await jsonOrThrow(resp);
    state.siem.tested = true;
    const nextBtn = document.getElementById('btnSiemNext');
    nextBtn.disabled = false;
    
    // Build success message with query execution details
    let successMessage = data.message || 'SIEM test succeeded';
    if (data.details && typeof data.details.result_count !== 'undefined') {
      const resultCount = data.details.result_count;
      if (resultCount === 0) {
        successMessage = `SIEM connection verified. Query executed successfully (0 results found).`;
      } else {
        successMessage = `SIEM connection verified. Query executed successfully (${resultCount} result${resultCount !== 1 ? 's' : ''}).`;
      }
    }
    
    setSuccess(successMessage);
    nextBtn.scrollIntoView({ behavior: 'smooth', block: 'center' });
  } catch (e) {
    state.siem.tested = false;
    document.getElementById('btnSiemNext').disabled = true;
    setAlert(e.message);
  } finally {
    if (siemSpinner) siemSpinner.classList.add('hidden');
    if (siemBtn) siemBtn.disabled = false;
  }
});

document.getElementById('btnSiemNext').addEventListener('click', async () => {
  setAlert('');
  setSuccess('');

  if (!state.siem.tested) {
    setAlert('Please test SIEM connection before continuing.');
    return;
  }

  try {
    const body = getSiemPayload();
    const resp = await fetch('/api/init/siem/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    await jsonOrThrow(resp);
    setSuccess('SIEM settings saved');
    setStep(2);
  } catch (e) {
    setAlert(e.message);
  }
});

// Step 2 buttons
document.getElementById('btnLlmBack').addEventListener('click', () => setStep(1));

document.getElementById('btnLlmTest').addEventListener('click', async () => {
  setAlert('');
  setSuccess('');
  const llmSpinner = document.getElementById('llmSpinner');
  const llmBtn = document.getElementById('btnLlmTest');
  if (llmSpinner) llmSpinner.classList.remove('hidden');
  if (llmBtn) llmBtn.disabled = true;

  try {
    const body = getLlmPayload();
    const resp = await fetch('/api/init/llm/test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await jsonOrThrow(resp);
    state.llm.tested = true;
    const nextBtn = document.getElementById('btnLlmNext');
    nextBtn.disabled = false;
    setSuccess(data.message || 'LLM test succeeded');
    nextBtn.scrollIntoView({ behavior: 'smooth', block: 'center' });
  } catch (e) {
    state.llm.tested = false;
    document.getElementById('btnLlmNext').disabled = true;
    setAlert(e.message);
  } finally {
    if (llmSpinner) llmSpinner.classList.add('hidden');
    if (llmBtn) llmBtn.disabled = false;
  }
});

document.getElementById('btnLlmNext').addEventListener('click', async () => {
  setAlert('');
  setSuccess('');

  if (!state.llm.tested) {
    setAlert('Please test the LLM before continuing.');
    return;
  }

  try {
    const body = getLlmPayload();
    const resp = await fetch('/api/init/llm/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    await jsonOrThrow(resp);
    updateReview();
    setSuccess('LLM settings saved');
    setStep(3);
  } catch (e) {
    setAlert(e.message);
  }
});

// Step 3 buttons
document.getElementById('btnReviewBack').addEventListener('click', () => setStep(2));

document.getElementById('btnFinish').addEventListener('click', async () => {
  setAlert('');
  setSuccess('');

  try {
    const resp = await fetch('/api/init/finish', { method: 'POST' });
    await jsonOrThrow(resp);

    statusBadge.textContent = 'Initialized';
    statusBadge.classList.remove('bg-gray-200', 'text-gray-700');
    statusBadge.classList.add('bg-green-500', 'text-white');

    setSuccess('Setup complete. Redirecting…');
    setTimeout(() => {
      window.location.href = '/';
    }, 700);
  } catch (e) {
    setAlert(e.message);
  }
});

// Initial state
setStep(1);
