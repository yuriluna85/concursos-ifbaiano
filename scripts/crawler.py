import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
from urllib.parse import urljoin

BASE_URL = "https://concurso.ifbaiano.edu.br/portal/"

def extrair_dados_edital(url):
    try:
        print(f"--- Acessando edital: {url}")
        response = requests.get(url, timeout=15)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')

        titulo = soup.find('h1').get_text(strip=True) if soup.find('h1') else "Edital sem título"
        tabela = soup.find('table')
        
        if not tabela:
            print(f"!!! Nenhuma tabela encontrada em: {url}")
            return None

        docs = []
        for linha in tabela.find_all('tr'):
            texto = linha.get_text(separator=' ', strip=True)
            # Busca o padrão de data: 00/00/0000 às 00h00
            match = re.search(r'(\d{2}/\d{2}/\d{4})\s+às\s+(\d{2}h\d{2})', texto)
            link = linha.find('a', href=True)

            if match and link:
                hora_limpa = match.group(2).replace('h', ':')
                data_obj = datetime.strptime(f"{match.group(1)} {hora_limpa}", "%d/%m/%Y %H:%M")
                docs.append({
                    "edital": titulo,
                    "documento": link.get_text(strip=True),
                    "link_doc": urljoin(url, link['href']),
                    "link_edital": url,
                    "data_hora": f"{match.group(1)} às {match.group(2)}",
                    "timestamp": data_obj.timestamp()
                })
        
        if docs:
            docs.sort(key=lambda x: x['timestamp'], reverse=True)
            print(f"✅ Sucesso: Encontrado '{docs[0]['documento']}'")
            return docs[0]
        
        return None
    except Exception as e:
        print(f"❌ Erro ao processar edital {url}: {e}")
        return None

def run():
    print("🚀 Iniciando varredura no Portal de Concursos...")
    try:
        res = requests.get(BASE_URL)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        links_editais = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            # Filtra links que parecem ser de pastas de editais (terminam em / e não são navegação)
            if not href.startswith('?') and not href.startswith('/') and href.endswith('/'):
                link_completo = urljoin(BASE_URL, href)
                links_editais.add(link_completo)

        print(f"🔍 Encontrados {len(links_editais)} links de possíveis editais.")

        resultados = []
        for link in list(links_editais)[:20]: # Limita aos 20 primeiros para teste rápido
            dados = extrair_dados_edital(link)
            if dados:
                resultados.append(dados)

        resultados.sort(key=lambda x: x['timestamp'], reverse=True)

        import os
        if not os.path.exists('data'):
            os.makedirs('data')

        with open('data/editais.json', 'w', encoding='utf-8') as f:
            json.dump(resultados, f, ensure_ascii=False, indent=4)
        
        print(f"🏁 Finalizado! {len(resultados)} editais salvos em data/editais.json")

    except Exception as e:
        print(f"🚨 Erro fatal no scraper: {e}")

if __name__ == "__main__":
    run()
