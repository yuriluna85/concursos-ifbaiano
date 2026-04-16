const container = document.getElementById('radar-container');
const buscador = document.getElementById('buscador');
const contador = document.getElementById('contador');
let db = [];

async function load() {
    try {
        const r = await fetch(`data/editais.json?v=${new Date().getTime()}`);
        db = await r.json();
        render(db);
    } catch {
        container.innerHTML = "<div class='card'><div class='doc-name'>Aguardando processamento...</div></div>";
    }
}

function render(list) {
    contador.innerText = list.length + " editais encontrados";
    if (list.length === 0) {
        container.innerHTML = "<p>Nenhum item encontrado.</p>";
        return;
    }
    container.innerHTML = list.map(i => `
        <a href="${i.link_edital}" target="_blank" class="card">
            <h3>${i.edital}</h3>
            <div class="doc-name">📄 ${i.documento}</div>
            <div class="date">🕒 Publicado: ${i.data_hora}</div>
        </a>
    `).join('');
}

buscador.addEventListener('input', (e) => {
    const val = e.target.value.toLowerCase();
    render(db.filter(i => i.edital.toLowerCase().includes(val) || i.documento.toLowerCase().includes(val)));
});

load();
