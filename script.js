const container = document.getElementById('radar-container');
const buscador = document.getElementById('buscador');
const statusTxt = document.getElementById('status-txt');
let dataStore = [];

async function sync() {
    try {
        // Tenta ler o last_run, mas verifica se é um texto válido e não HTML
        const resRun = await fetch(`data/last_run.txt?t=${Date.now()}`);
        if (resRun.ok) {
            const text = await resRun.text();
            if (!text.includes("<!DOCTYPE html>")) {
                statusTxt.innerText = "Última varredura: " + text;
            }
        }

        const resData = await fetch(`data/editais.json?t=${Date.now()}`);
        if (!resData.ok) throw new Error();
        dataStore = await resData.json();
        render(dataStore);
    } catch {
        container.innerHTML = "<div class='card'><div class='doc-name'>Aguardando processamento...</div><div class='date'>O robô está trabalhando. Tente novamente em instantes.</div></div>";
    }
}

function render(list) {
    if (!list || list.length === 0) {
        container.innerHTML = "<p style='text-align:center; grid-column:1/-1;'>Nenhum edital encontrado recentemente.</p>";
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
    const term = e.target.value.toLowerCase();
    render(dataStore.filter(i => i.edital.toLowerCase().includes(term) || i.documento.toLowerCase().includes(term)));
});

sync();
