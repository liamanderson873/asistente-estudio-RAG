const byId = id => document.getElementById(id);
async function refreshStatus() {
  const button = byId('retry-services');
  button.disabled = true;
  byId('services-status').textContent = 'Comprobando servicios locales…';
  try {
    const status = await api('/api/status');
    byId('services-status').textContent = status.ready
      ? 'Todo listo para estudiar.'
      : `${status.database.message} ${status.ollama.message}`;
  } catch (error) {
    byId('services-status').textContent = 'No se puede comprobar la conexión con el asistente.';
  } finally { button.disabled = false; }
}
async function api(path, options) {
  const response = await fetch(path, options);
  const body = await response.json();
  if (!response.ok) {
    throw new Error(typeof body.detail === 'string' ? body.detail : 'Revisa los datos introducidos.');
  }
  return body;
}
async function refreshDocuments() {
  const list = byId('documents');
  try {
    const documents = await api('/api/documents');
    list.replaceChildren();
    if (!documents.length) {
      const item = document.createElement('li');
      item.textContent = 'Tu biblioteca está vacía. Añade el primer documento.';
      list.append(item);
    }
    for (const doc of documents) {
      const item = document.createElement('li');
      const link = document.createElement('a');
      link.href = `/api/documents/${encodeURIComponent(doc.id)}/pdf`;
      link.target = '_blank'; link.rel = 'noopener'; link.textContent = doc.name;
      const detail = document.createElement('small');
      detail.textContent = `${doc.pages} páginas`;
      item.append(link, detail); list.append(item);
    }
  } catch (error) { list.textContent = error.message; }
}
byId('upload-form').addEventListener('submit', async event => {
  event.preventDefault();
  const button = event.target.querySelector('button'); button.disabled = true;
  byId('upload-status').textContent = 'Leyendo el PDF y preparando su búsqueda. Puede tardar…';
  try {
    const result = await api('/api/documents', {method: 'POST', body: new FormData(event.target)});
    byId('upload-status').textContent = result.duplicate ? 'Este documento ya estaba en la biblioteca.' : `Documento añadido · ${result.pages} páginas.`;
    await refreshDocuments();
  } catch (error) { byId('upload-status').textContent = error.message; }
  finally { button.disabled = false; }
});
byId('question-form').addEventListener('submit', async event => {
  event.preventDefault();
  const button = event.target.querySelector('button'); button.disabled = true;
  byId('question-status').textContent = 'Buscando fuentes y preparando la respuesta…';
  byId('answer').hidden = true;
  try {
    const result = await api('/api/ask', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({question: byId('question').value, mode: byId('mode').value})});
    byId('empty-answer').hidden = true;
    byId('answer-text').textContent = result.answer;
    const citations = byId('citations'); citations.replaceChildren();
    for (const citation of result.citations) {
      const card = document.createElement('div'); card.className = 'citation';
      const link = document.createElement('a'); link.href = citation.url;
      link.target = '_blank'; link.rel = 'noopener';
      link.textContent = `${citation.document} · página ${citation.page}`;
      const excerpt = document.createElement('p'); excerpt.textContent = citation.excerpt;
      card.append(link, excerpt); citations.append(card);
    }
    if (result.abstained) citations.textContent = 'No hay fuentes suficientes para esta respuesta.';
    byId('answer').hidden = false;
    byId('question-status').textContent = result.abstained ? 'No se ha generado una respuesta con fuentes.' : 'Respuesta preparada. Comprueba las referencias.';
  } catch (error) { byId('question-status').textContent = error.message; }
  finally { button.disabled = false; }
});
refreshDocuments();
refreshStatus();
byId('retry-services').addEventListener('click', () => {
  refreshStatus();
  refreshDocuments();
});
