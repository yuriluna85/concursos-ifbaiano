import requests
from bs4 import BeautifulSoup
import json
import re
import os
from datetime import datetime, timedelta
from urllib.parse import urljoin
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'}
BASE_URL = "https://ifbaiano.edu.br/portal/concursos/"

def tratar_data(txt):
    agora = datetime.now()
    txt = txt.lower()
    m_hora = re.search(r'(\d{1,2})h(\d{2})', txt)
    h, m = (int(m_hora.group(1)), int(m_hora.group(2))) if m_hora else (0, 0)
    
    m_data = re.search(r'(\d{2}/\d{2}/\d{4})', txt)
    if 'hoje' in txt: dt = agora
    elif 'ontem' in txt: dt = agora - timedelta(days=1)
    elif m_data:
        try: return datetime.strptime(f"{m_data.group(1)} {h}:{m}", "%d/%m/%Y %H:%M")
        except: return agora
    else: return agora
    
    return dt.replace(hour=h, minute=m, second=0, microsecond=0)

def extrair_titulo_rico(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=12, verify=False)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        alvo = soup.find('h1') or soup.find('h2') or soup.find('strong')
        return alvo.get_text(strip=True) if alvo else "Edital Institucional"
    except: return "Edital (Ver no Portal)"

def run():
    print(f"🚀 Verificando portal real: {BASE_URL}")
    os.makedirs('data', exist_ok=True)
    
    # GARANTE QUE O ARQUIVO DE STATUS EXISTE
    with open('data/last_run.txt', 'w') as f:
        f.write(datetime.now().strftime("%d/%m/%Y às %H:%M"))

    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=30, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        editais_brutos = []
        # Captura links que pareçam ser de editais (mesmo que não tenham a URL completa)
        for a in soup.find_all('a', href=True):
            href = a['href']
            # Se o link for para o portal de concursos ou tiver "edital" no nome
            if 'concurso' in href.lower() or 'edital' in href.lower():
                full_url = urljoin(BASE_URL, href)
                if full_url == BASE_URL: continue
                
                pai = a.find_parent(['div', 'li', 'tr', 'p', 'article'])
                txt_pai = pai.get_text(separator=' ', strip=True) if pai else "Hoje"
                
                dt = tratar_data(txt_pai)
                editais_brutos.append({
                    "url": full_url,
                    "doc": a.get_text(strip=True) or "Acessar Documentos",
                    "ts": dt.timestamp(),
                    "dt_str": dt.strftime("%d/%m/%Y às %H:%M")
                })

        # Remove duplicados e pega o top 10
        vistos = set()
        unicos = []
        for e in sorted(editais_brutos, key=lambda x: x['ts'], reverse=True):
            if e['url'] not in vistos:
                vistos.add(e['url'])
                unicos.append(e)

        final = []
        for item in unicos[:10]:
            print(f"🔎 Lendo título: {item['url']}")
            t = extrair_titulo_rico(item['url'])
            final.append({
                "edital": t,
                "documento": item['doc'],
                "link_edital": item['url'],
                "data_hora": item['dt_str'],
                "timestamp": item['ts']
            })

        with open('data/editais.json', 'w', encoding='utf-8') as f:
            json.dump(final, f, ensure_ascii=False, indent=4)
            
        print(f"🏁 Concluído: {len(final)} editais salvos.")
    except Exception as e:
        print(f"🚨 Erro: {e}")

if __name__ == "__main__":
    run()
