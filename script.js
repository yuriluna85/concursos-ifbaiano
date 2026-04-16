const container = document.getElementById('radar-container');
const buscador = document.getElementById('buscador');
const footerStatus = document.getElementById('ultima-verificacao');
let dataStore = [];

async function fetchData() {
    try {
        // Tenta ler o last_run para saber quando o robô rodou
        const runRes = await fetch(`data/last_run.txt?t=${Date.now()}`);
        const lastRun = await runRes.text();
        footerStatus.innerText = "Última varredura do robô: " + lastRun;

        // Carrega os editais
        const res = await fetch(`data/editais.json?t=${Date.now()}`);
        dataStore = await res.json();
        render(dataStore);
    } catch {
        container.innerHTML = "<div class='card'><div class='doc-name'>Robô em patrulha...</div><div class='date'>Aguardando a próxima atualização de 30 minutos.</div></div>";
    }
}

function render(list) {
    if (list.length === 0) {
        container.innerHTML = "<p style='text-align:center; grid-column:1/-1;'>O robô não encontrou atualizações nas últimas horas.</p>";
        return;
    }
    container.innerHTML = list.map(i => `
        <a href="${i.link_edital}" target="_blank" class="card">
            <h3>${i.edital}</h3>
            <div class="doc-name">📄 ${i.documento}</div>
            <div class="date">🕒 Postado em: ${i.data_hora}</div>
        </a>
    `).join('');
}

buscador.addEventListener('input', (e) => {
    const term = e.target.value.toLowerCase();
    render(dataStore.filter(i => i.edital.toLowerCase().includes(term) || i.documento.toLowerCase().includes(term)));
});

fetchData();
