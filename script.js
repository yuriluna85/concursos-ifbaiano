const container = document.getElementById('radar-container');
const buscador = document.getElementById('buscador');
let todosEditais = [];

async function carregarDados() {
    try {
        const response = await fetch('./data/editais.json');
        todosEditais = await response.json();
        renderizar(todosEditais);
    } catch (e) {
        container.innerHTML = "<p>Erro ao carregar dados. Tente novamente mais tarde.</p>";
    }
}

function renderizar(lista) {
    container.innerHTML = lista.map(item => `
        <a href="${item.link_edital}" target="_blank" class="card">
            <div>
                <h3>${item.edital}</h3>
                <div class="doc-name">📄 ${item.documento}</div>
            </div>
            <div class="date">📅 Postado em: ${item.data_hora}</div>
        </a>
    `).join('');
}

buscador.addEventListener('input', (e) => {
    const termo = e.target.value.toLowerCase();
    const filtrados = todosEditais.filter(i => 
        i.edital.toLowerCase().includes(termo) || 
        i.documento.toLowerCase().includes(termo)
    );
    renderizar(filtrados);
});

carregarDados();
