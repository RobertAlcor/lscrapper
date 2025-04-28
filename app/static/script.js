document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('scrape-form');
  const btn = document.getElementById('go-btn');
  const btnText = document.getElementById('btn-text');
  const btnSpinner = document.getElementById('btn-spinner');
  const progressBar = document.getElementById('progress-bar');
  const leadCount = document.getElementById('leadcount-value');
  const logsList = document.getElementById('logs-list');
  const original = btnText.textContent;

  form.addEventListener('submit', e => {
    e.preventDefault();
    // UI zurücksetzen
    btn.disabled = true;
    btnSpinner.classList.remove('d-none');
    btnText.textContent = 'Sammle…';
    progressBar.style.width = '0%';
    progressBar.textContent = '0%';
    leadCount.textContent = '0';
    logsList.innerHTML = '';

    // Werte
    const site = form.website.value.trim();
    const pages = form.seiten.value;
    const fields = Array.from(form.querySelectorAll('input[name="felder"]:checked'))
      .map(cb => cb.value)
      .join(',');

    // SSE öffnen
    const es = new EventSource(
      `/scrape-stream?site=${encodeURIComponent(site)}&pages=${pages}&fields=${fields}`
    );
    let totalLeads = 0;

    es.addEventListener('progress', ev => {
      const d = JSON.parse(ev.data);
      const pct = Math.round((d.page / d.total) * 100);
      progressBar.style.width = pct + '%';
      progressBar.textContent = pct + '%';
      logsList.insertAdjacentHTML('beforeend', `<li>Seite ${d.page}: ${d.found} Einträge</li>`);
    });

    es.addEventListener('lead', ev => {
      const lead = JSON.parse(ev.data);
      totalLeads++;
      leadCount.textContent = totalLeads;
      logsList.insertAdjacentHTML('beforeend', `<li>Lead: <strong>${lead.Firma}</strong></li>`);
    });

    es.addEventListener('done', ev => {
      const { filename } = JSON.parse(ev.data);
      logsList.insertAdjacentHTML('beforeend', `<li><strong>Fertig!</strong> Datei: ${filename}</li>`);
      // CSV automatisch downloaden
      fetch('/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename })
      })
        .then(r => r.blob())
        .then(blob => {
          const a = document.createElement('a');
          a.href = URL.createObjectURL(blob);
          a.download = filename;
          document.body.appendChild(a);
          a.click();
          a.remove();
        });
      // UI zurücksetzen
      btnSpinner.classList.add('d-none');
      btnText.textContent = original;
      btn.disabled = false;
      es.close();
    });

    es.onerror = () => {
      logsList.insertAdjacentHTML('beforeend', '<li class="text-danger">Fehler beim Stream</li>');
      btnSpinner.classList.add('d-none');
      btnText.textContent = original;
      btn.disabled = false;
      es.close();
    };
  });
});
