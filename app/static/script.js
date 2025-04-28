document.addEventListener('DOMContentLoaded', function () {
  const form = document.getElementById('scrape-form');
  const btn = document.getElementById('go-btn');
  const btnText = document.getElementById('btn-text');
  const btnSpinner = document.getElementById('btn-spinner');
  const progressBar = document.getElementById('progress-bar');
  const leadCountElem = document.getElementById('leadcount-value');
  const logsList = document.getElementById('logs-list');
  const originalText = btnText.textContent;
  let pollInterval;

  form.addEventListener('submit', function (e) {
    // Button-Disable & Spinner anzeigen
    btn.disabled = true;
    btnSpinner.classList.remove('d-none');
    btnText.textContent = 'Sammle…';
    // Progress-Bar animieren
    progressBar.classList.add('progress-bar-striped', 'progress-bar-animated');
    // Polling starten
    pollInterval = setInterval(updateStatus, 1000);
  });

  function updateStatus() {
    // 1) Fortschritt abrufen
    fetch('/progress')
      .then(res => res.json())
      .then(data => {
        const pct = data.progress;
        progressBar.style.width = pct + '%';
        progressBar.textContent = pct + '%';
        if (pct >= 100) finishPolling();
      })
      .catch(console.error);

    // 2) Lead-Anzahl abrufen
    fetch('/leadcount')
      .then(res => res.json())
      .then(data => {
        leadCountElem.textContent = data.lead_count;
      })
      .catch(console.error);

    // 3) Logs abrufen
    fetch('/logs')
      .then(res => res.json())
      .then(data => {
        logsList.innerHTML = '';
        data.logs.forEach(msg => {
          const li = document.createElement('li');
          li.textContent = msg;
          logsList.appendChild(li);
        });
      })
      .catch(console.error);
  }

  function finishPolling() {
    clearInterval(pollInterval);
    btnSpinner.classList.add('d-none');
    btnText.textContent = originalText;
    btn.disabled = false;
    progressBar.classList.remove('progress-bar-animated');
    // optional: progressBar.classList.remove('progress-bar-striped');
  }
});
