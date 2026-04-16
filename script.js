const container = document.getElementById('radar-container');
const buscador = document.getElementById('buscador');
const statusTxt = document.getElementById('status-txt');
let dataStore = [];

async function sync() {
    try {
        const resRun = await fetch(`data/last_run.txt?nocache=${Date.now()}`);
        if (resRun.ok) {
            const text = await resRun.text();
            if (!text.includes("<!DOCTYPE html>")) {
                statusTxt.innerText = "Última sincronização WP: " + text;
            }
        }

        const resData = await fetch(`data/editais.json?nocache=${Date.now()}`);
        if (!resData.ok) throw new Error();
        
        dataStore = await resData.json();
        render(dataStore);
    } catch (e) {
        container.innerHTML = `
            <div class='card' style='border-color: #e74c3c;'>
                <div class='doc-name'>Aguardando processamento</div>
                <div class='date'>Conectando à API do WordPress. Volte em alguns minutos.</div>
            </div>`;
    }
}

function render(list) {
    if (!list || list.length === 0) {
        container.innerHTML = "<p style='text-align:center; grid-column:1/-1;'>Nenhum documento encontrado.</p>";
        return;
    }
    
    // Agora o card tem dois botões: um para o PDF e outro para a página do Edital
    container.innerHTML = list.map(i => `
        <div class="card">
            <h3>${i.edital}</h3>
            <div class="date">🕒 ${i.data_hora}</div>
            <div class="doc-name">📄 ${i.documento}</div>
            
            <div class="botoes">
                <a href="${i.link_doc}" target="_blank" class="btn btn-doc">⏬ ABRIR ARQUIVO</a>
                <a href="${i.link_edital}" target="_blank" class="btn btn-edital">VER EDITAL</a>
            </div>
        </div>
    `).join('');
}

buscador.addEventListener('input', (e) => {
    const term = e.target.value.toLowerCase();
    render(dataStore.filter(i => i.edital.toLowerCase().includes(term) || i.documento.toLowerCase().includes(term)));
});

sync();
