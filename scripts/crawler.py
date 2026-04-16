import requests
from bs4 import BeautifulSoup
import json
import re
import os
from datetime import datetime, timedelta
from urllib.parse import urljoin
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}
BASE_URL = "https://ifbaiano.edu.br/portal/concursos/"

def tratar_data(txt):
    agora = datetime.now()
    txt = txt.lower()
    m_hora = re.search(r'(\d{1,2})h(\d{2})', txt)
    h, m = (int(m_hora.group(1)), int(m_hora.group(2))) if m_hora else (0, 0)
    if 'hoje' in txt: dt = agora
    elif 'ontem' in txt: dt = agora - timedelta(days=1)
    else:
        m_data = re.search(r'(\d{2}/\d{2}/\d{4})', txt)
        if m_data:
            try: return datetime.strptime(f"{m_data.group(1)} {h}:{m}", "%d/%m/%Y %H:%M")
            except: return agora
        return agora
    return dt.replace(hour=h, minute=m, second=0, microsecond=0)

def extrair_titulo_rico(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=10, verify=False)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        alvo = soup.find('h1') or soup.find('strong')
        return alvo.get_text(strip=True) if alvo else "Edital Interno"
    except: return "Edital"

def run():
    print("🚀 Iniciando Coleta Flash (Top 10)...")
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=20, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        editais_raw = []
        blocos = soup.find_all(['article', 'div'], class_=re.compile(r'post|item|edital'))

        for bloco in blocos:
            link_tag = bloco.find('a', href=True)
            if not link_tag: continue
            url = urljoin(BASE_URL, link_tag['href'])
            if 'concurso.ifbaiano.edu.br/portal/' not in url: continue
            
            txt_bloco = bloco.get_text(separator=' ', strip=True)
            dt_obj = tratar_data(txt_bloco)
            
            # Pega o texto do último elemento para o nome do documento
            partes = bloco.get_text(separator='|', strip=True).split('|')
            doc_nome = partes[-1] if len(partes) > 1 else "Nova Atualização"

            editais_raw.append({
                "url": url,
                "doc": doc_nome,
                "timestamp": dt_obj.timestamp(),
                "data_txt": dt_obj.strftime("%d/%m/%Y às %H:%M")
            })

        # Ordena para pegar os 10 mais novos ANTES de entrar nos links (ganha tempo)
        editais_raw.sort(key=lambda x: x['timestamp'], reverse=True)
        top_10 = editais_raw[:10]

        final = []
        for item in top_10:
            print(f"🔎 Enriquecendo título: {item['url']}")
            titulo = extrair_titulo_rico(item['url'])
            final.append({
                "edital": titulo,
                "documento": item['doc'],
                "link_edital": item['url'],
                "data_hora": item['data_txt'],
                "timestamp": item['timestamp']
            })

        os.makedirs('data', exist_ok=True)
        with open('data/editais.json', 'w', encoding='utf-8') as f:
            json.dump(final, f, ensure_ascii=False, indent=4)
        print(f"🏁 Finalizado! {len(final)} itens salvos.")
    except Exception as e: print(f"🚨 Erro: {e}")

if __name__ == "__main__":
    run()
