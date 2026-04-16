import requests
from bs4 import BeautifulSoup
import json
import re
import os
from datetime import datetime, timedelta
from urllib.parse import urljoin

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
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
        res = requests.get(url, headers=HEADERS, timeout=15)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        h1 = soup.find('h1')
        if h1:
            titulo = h1.get_text(strip=True)
            if "Edital" in titulo and len(titulo) < 35:
                strong = soup.find('strong')
                if strong: titulo = strong.get_text(strip=True)
            return titulo
        return "Edital de Concurso"
    except:
        return "Edital"

def run():
    print(f"🚀 Iniciando busca em: {BASE_URL}")
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        resultados = []

        links_vistos = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            if 'concurso.ifbaiano.edu.br/portal/' in href and href not in links_vistos:
                links_vistos.add(href)
                pai = a.find_parent(['div', 'li', 'tr', 'p'])
                texto_data = pai.get_text() if pai else "Hoje às 00h00"
                
                print(f"🔎 Analisando edital: {href}")
                titulo = extrair_titulo_rico(href)
                dt_obj = tratar_data_relativa(texto_data)

                resultados.append({
                    "edital": titulo,
                    "documento": "Ver documentos atualizados no portal",
                    "link_doc": href,
                    "link_edital": href,
                    "data_hora": dt_obj.strftime("%d/%m/%Y às %H:%M"),
                    "timestamp": dt_obj.timestamp()
                })

        resultados.sort(key=lambda x: x['timestamp'], reverse=True)
        os.makedirs('data', exist_ok=True)
        with open('data/editais.json', 'w', encoding='utf-8') as f:
            json.dump(resultados, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"🚨 Erro: {e}")

if __name__ == "__main__":
    run()
