const container = document.getElementById('radar-container');
const buscador = document.getElementById('buscador');
const footerTime = document.getElementById('ultima-verificacao');
let dados = [];

async function sync() {
    try {
        const r = await fetch(`data/editais.json?nocache=${Date.now()}`);
        dados = await r.json();
        render(dados);
        footerTime.innerText = "Última sincronização: " + new Date().toLocaleTimeString();
    } catch {
        container.innerHTML = "<div class='card'><div class='doc-name'>Aguardando primeira execução do robô...</div></div>";
    }
}

function render(list) {
    if (list.length === 0) {
        container.innerHTML = "<p>Nenhum documento recente.</p>";
        return;
    }
    container.innerHTML = list.map(i => `
        <a href="${i.link_edital}" target="_blank" class="card">
            <h3>${i.edital}</h3>
            <div class="doc-name">📄 ${i.documento}</div>
            <div class="date">🕒 ${i.data_hora}</div>
        </a>
    `).join('');
}

buscador.addEventListener('input', (e) => {
    const v = e.target.value.toLowerCase();
    render(dados.filter(i => i.edital.toLowerCase().includes(v) || i.documento.toLowerCase().includes(v)));
});

sync();
