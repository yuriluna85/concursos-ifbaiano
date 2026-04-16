const container = document.getElementById('radar-container');
const buscador = document.getElementById('buscador');
let store = [];

async function init() {
    try {
        // Cache busting para garantir que pegamos o JSON mais novo
        const res = await fetch(`data/editais.json?t=${new Date().getTime()}`);
        if (!res.ok) throw new Error();
        store = await res.json();
        render(store);
    } catch {
        container.innerHTML = `
            <div class="card">
                <div class="doc-name">Sincronizando dados...</div>
                <div class="date">O robô está lendo o portal do IF Baiano agora. Atualize a página em 1 minuto.</div>
            </div>`;
    }
}

function render(data) {
    if (!data || data.length === 0) {
        container.innerHTML = "<p style='text-align:center; grid-column: 1/-1;'>Nenhum edital recente encontrado no portal.</p>";
        return;
    }
    container.innerHTML = data.map(i => `
        <a href="${i.link_edital}" target="_blank" class="card">
            <h3>${i.edital}</h3>
            <div class="doc-name">📄 ${i.documento}</div>
            <div class="date">🕒 Publicado em: ${i.data_hora}</div>
        </a>
    `).join('');
}

buscador.addEventListener('input', (e) => {
    const val = e.target.value.toLowerCase();
    render(store.filter(i => i.edital.toLowerCase().includes(val) || i.documento.toLowerCase().includes(val)));
});

init();
