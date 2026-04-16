import requests
from bs4 import BeautifulSoup
import json
import re
import os
from datetime import datetime, timedelta
from urllib.parse import urljoin
import urllib3

# Desabilita avisos de SSL inseguro (comum em portais do governo)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}

BASE_URL = "https://ifbaiano.edu.br/portal/concursos/"

def tratar_data_relativa(texto_data):
    agora = datetime.now()
    texto_data = texto_data.lower()
    match_hora = re.search(r'(\d{1,2})h(\d{2})', texto_data)
    h, m = (int(match_hora.group(1)), int(match_hora.group(2))) if match_hora else (0, 0)
    
    if 'hoje' in texto_data:
        dt = agora
    elif 'ontem' in texto_data:
        dt = agora - timedelta(days=1)
    else:
        match_data = re.search(r'(\d{2}/\d{2}/\d{4})', texto_data)
        if match_data:
            try: return datetime.strptime(f"{match_data.group(1)} {h}:{m}", "%d/%m/%Y %H:%M")
            except: return agora
        return agora
    return dt.replace(hour=h, minute=m, second=0, microsecond=0)

def extrair_titulo_rico(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=15, verify=False)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        h1 = soup.find('h1')
        if h1:
            titulo = h1.get_text(strip=True)
            if len(titulo) < 35:
                strong = soup.find('strong')
                if strong: titulo = strong.get_text(strip=True)
            return titulo
        return "Edital de Concurso"
    except:
        return "Edital (Link Externo)"

def run():
    print(f"🚀 Verificando: {BASE_URL}")
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=30, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        resultados = []
        links_vistos = set()

        # Busca por links que contenham padrões de concursos ou apontem para o subdomínio
        for a in soup.find_all('a', href=True):
            href = a['href']
            link_full = urljoin(BASE_URL, href)

            # Filtro mais aberto: links que contêm 'concurso' ou 'portal' no caminho
            if ('concurso' in link_full or 'portal' in link_full) and link_full not in links_vistos:
                if link_full == BASE_URL: continue
                
                links_vistos.add(link_full)
                pai = a.find_parent(['div', 'li', 'tr', 'p', 'article'])
                texto_item = pai.get_text() if pai else "Hoje"

                if any(p in texto_item.lower() for p in ['hoje', 'ontem', '/202']):
                    print(f"🔎 Capturando: {link_full}")
                    titulo = extrair_titulo_rico(link_full)
                    dt_obj = tratar_data_relativa(texto_item)

                    resultados.append({
                        "edital": titulo,
                        "documento": "Clique para ver arquivos atualizados",
                        "link_doc": link_full,
                        "link_edital": link_full,
                        "data_hora": dt_obj.strftime("%d/%m/%Y às %H:%M"),
                        "timestamp": dt_obj.timestamp()
                    })

        resultados.sort(key=lambda x: x['timestamp'], reverse=True)
        os.makedirs('data', exist_ok=True)
        with open('data/editais.json', 'w', encoding='utf-8') as f:
            json.dump(resultados, f, ensure_ascii=False, indent=4)
        print(f"🏁 Finalizado! {len(resultados)} itens salvos.")
    except Exception as e:
        print(f"🚨 Erro fatal: {e}")

if __name__ == "__main__":
    run()
