import requests
from bs4 import BeautifulSoup
import json
import re
import os
from datetime import datetime
from urllib.parse import urljoin

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

BASE_URL = "https://concurso.ifbaiano.edu.br/portal/"

def extrair_dados_edital(url):
    try:
        # verify=False ajuda se o certificado SSL do portal estiver instável
        response = requests.get(url, headers=HEADERS, timeout=20, verify=True)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')

        titulo = soup.find('h1').get_text(strip=True) if soup.find('h1') else "Sem Título"
        
        docs = []
        # O IF Baiano costuma usar tabelas ou listas para os editais
        elementos_busca = soup.find_all(['tr', 'li', 'p'])
        
        for el in elementos_busca:
            texto = el.get_text(separator=' ', strip=True)
            # Regex ajustada para o padrão: 14/04/2026 às 09h11
            match = re.search(r'(\d{2}/\d{2}/\d{4})\s+às\s+(\d{2}h\d{2})', texto)
            link = el.find('a', href=True)

            if match and link:
                href_doc = link['href'].lower()
                # Só pega se for arquivo
                if href_doc.endswith(('.pdf', '.docx', '.odt', '.doc', '.zip')):
                    hora_limpa = match.group(2).replace('h', ':')
                    try:
                        data_obj = datetime.strptime(f"{match.group(1)} {hora_limpa}", "%d/%m/%Y %H:%M")
                        docs.append({
                            "edital": titulo,
                            "documento": link.get_text(strip=True),
                            "link_doc": urljoin(url, link['href']),
                            "link_edital": url,
                            "data_hora": f"{match.group(1)} às {match.group(2)}",
                            "timestamp": data_obj.timestamp()
                        })
                    except: continue
        
        if docs:
            docs.sort(key=lambda x: x['timestamp'], reverse=True)
            return docs[0]
        return None
    except Exception as e:
        print(f"Erro no edital {url}: {e}")
        return None

def run():
    print(f"🚀 Iniciando busca em: {BASE_URL}")
    try:
        res = requests.get(BASE_URL, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(res.text, 'html.parser')
        links_editais = set()

        for a in soup.find_all('a', href=True):
            href = a['href']
            # Agora aceitamos links que contenham 'portal' e terminem com /
            full_link = urljoin(BASE_URL, href)
            
            # Garante que o link é interno do portal e não é a raiz
            if full_link.startswith(BASE_URL) and full_link != BASE_URL:
                if href.endswith('/') and not href.startswith('?'):
                    links_editais.add(full_link)
        
        print(f"🔍 Encontrados {len(links_editais)} editais potenciais.")

        resultados = []
        for idx, link in enumerate(list(links_editais)):
            print(f"[{idx+1}/{len(links_editais)}] Analisando: {link}")
            dados = extrair_dados_edital(link)
            if dados:
                print(f"   ✅ Documento encontrado: {dados['documento']}")
                resultados.append(dados)

        resultados.sort(key=lambda x: x['timestamp'], reverse=True)

        os.makedirs('data', exist_ok=True)
        with open('data/editais.json', 'w', encoding='utf-8') as f:
            json.dump(resultados, f, ensure_ascii=False, indent=4)
        
        print(f"🏁 Fim! {len(resultados)} editais com documentos novos.")

    except Exception as e:
        print(f"🚨 Erro na raiz: {e}")

if __name__ == "__main__":
    run()
