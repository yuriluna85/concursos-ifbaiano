const container = document.getElementById('radar-container');
const buscador = document.getElementById('buscador');
let todosDados = [];

async function carregar() {
    try {
        const res = await fetch('data/editais.json');
        if (!res.ok) throw new Error();
        todosDados = await res.json();
        exibir(todosDados);
    } catch {
        container.innerHTML = `<div class="card"><div class="doc-name">Aguardando dados...</div><div class="date">O robô está processando as informações. Tente recarregar em instantes.</div></div>`;
    }
}

function exibir(lista) {
    if (lista.length === 0) {
        container.innerHTML = "<p>Nenhum edital encontrado.</p>";
        return;
    }
    container.innerHTML = lista.map(item => `
        <a href="${item.link_edital}" target="_blank" class="card">
            <h3>${item.edital}</h3>
            <div class="doc-name">📄 ${item.documento}</div>
            <div class="date">🕒 Publicado em: ${item.data_hora}</div>
        </a>
    `).join('');
}

buscador.addEventListener('input', (e) => {
    const termo = e.target.value.toLowerCase();
    const filtrados = todosDados.filter(i => 
        i.edital.toLowerCase().includes(termo) || 
        i.documento.toLowerCase().includes(termo)
    );
    exibir(filtrados);
});

carregar();
