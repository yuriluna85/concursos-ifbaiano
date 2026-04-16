import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime

# URLs de monitoramento
BASE_URL = "https://concurso.ifbaiano.edu.br/portal/"

def extrair_dados_edital(url):
    try:
        response = requests.get(url, timeout=15)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')

        titulo = soup.find('h1').get_text(strip=True) if soup.find('h1') else "Edital sem título"
        tabela = soup.find('table')
        if not tabela: return None

        docs = []
        for linha in tabela.find_all('tr'):
            texto = linha.get_text(separator=' ', strip=True)
            match = re.search(r'(\d{2}/\d{2}/\d{4})\s+às\s+(\d{2}h\d{2})', texto)
            link = linha.find('a', href=True)

            if match and link:
                data_obj = datetime.strptime(f"{match.group(1)} {match.group(2).replace('h', ':')}", "%d/%m/%Y %H:%M")
                docs.append({
                    "edital": titulo,
                    "documento": link.get_text(strip=True),
                    "link_doc": link['href'],
                    "link_edital": url,
                    "data_hora": f"{match.group(1)} às {match.group(2)}",
                    "timestamp": data_obj.timestamp()
                })
        
        return sorted(docs, key=lambda x: x['timestamp'], reverse=True)[0] if docs else None
    except:
        return None

def run():
    print("Iniciando varredura...")
    res = requests.get(BASE_URL)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # Busca links de editais na página principal (pastas do portal)
    links_editais = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        if BASE_URL in href and href != BASE_URL:
            links_editais.add(href)

    resultados = []
    for link in links_editais:
        print(f"Analisando: {link}")
        dados = extrair_dados_edital(link)
        if dados: resultados.append(dados)

    # Ordena todos os resultados pelo mais recente globalmente
    resultados.sort(key=lambda x: x['timestamp'], reverse=True)

    with open('data/editais.json', 'w', encoding='utf-8') as f:
        json.dump(resultados, f, ensure_ascii=False, indent=4)
    print("Dados salvos com sucesso!")

if __name__ == "__main__":
    run()
