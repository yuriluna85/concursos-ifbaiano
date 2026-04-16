const container = document.getElementById('radar-container');
const buscador = document.getElementById('buscador');
let dadosOriginais = [];

async function carregarDados() {
    try {
        const res = await fetch('data/editais.json');
        if (!res.ok) throw new Error();
        dadosOriginais = await res.json();
        renderizar(dadosOriginais);
    } catch {
        container.innerHTML = `<div class="card"><div class="doc-name">Nenhum dado encontrado ainda.</div><div class="date">Aguarde o robô processar...</div></div>`;
    }
}

function renderizar(lista) {
    if (lista.length === 0) {
        container.innerHTML = "<p>Nenhum edital encontrado para sua busca.</p>";
        return;
    }
    container.innerHTML = lista.map(item => `
        <a href="${item.link_edital}" target="_blank" class="card">
            <div>
                <h3>${item.edital}</h3>
                <div class="doc-name">📄 ${item.documento}</div>
            </div>
            <div class="date">🕒 Publicado em: ${item.data_hora}</div>
        </a>
    `).join('');
}

buscador.addEventListener('input', (e) => {
    const termo = e.target.value.toLowerCase();
    const filtrados = dadosOriginais.filter(i => 
        i.edital.toLowerCase().includes(termo) || 
        i.documento.toLowerCase().includes(termo)
    );
    renderizar(filtrados);
});

carregarDados();
