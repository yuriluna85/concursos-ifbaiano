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
    
    if 'hoje' in txt: dt = agora
    elif 'ontem' in txt: dt = agora - timedelta(days=1)
    else:
        m_data = re.search(r'(\d{2}/\d{2}/\d{4})', txt)
        if m_data:
            try: return datetime.strptime(f"{match_data.group(1)} {h}:{m}", "%d/%m/%Y %H:%M")
            except: return agora
        return agora
    return dt.replace(hour=h, minute=m, second=0, microsecond=0)

def extrair_titulo_rico(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=12, verify=False)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        # Tenta pegar o H1 ou a primeira tag de destaque do portal de concursos
        titulo = soup.find('h1') or soup.find('h2') or soup.find('strong')
        return titulo.get_text(strip=True) if titulo else "Edital Institucional"
    except: return "Acesse para detalhes"

def run():
    print(f"🕵️ Investigando portal: {BASE_URL}")
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=30, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        editais_encontrados = []
        # Busca TODOS os links da página para não deixar nada passar
        todos_links = soup.find_all('a', href=True)
        print(f"📊 Total de links encontrados na página: {len(todos_links)}")

        for link in todos_links:
            href = link['href']
            # Filtra apenas links que levam para o subdomínio de concursos
            if 'concurso.ifbaiano.edu.br/portal/' in href:
                pai = link.find_parent(['div', 'li', 'tr', 'p', 'article'])
                texto_contexto = pai.get_text(separator=' ', strip=True) if pai else "Hoje"
                
                dt_obj = tratar_data(texto_contexto)
                
                editais_encontrados.append({
                    "url": urljoin(BASE_URL, href),
                    "texto": link.get_text(strip=True) or "Ver Edital",
                    "timestamp": dt_obj.timestamp(),
                    "data_txt": dt_obj.strftime("%d/%m/%Y às %H:%M")
                })

        # Remove duplicatas de URL e pega os 10 mais recentes
        vistos = set()
        unicos = []
        for e in sorted(editais_encontrados, key=lambda x: x['timestamp'], reverse=True):
            if e['url'] not in vistos:
                vistos.add(e['url'])
                unicos.append(e)
        
        top_10 = unicos[:10]
        print(f"✅ Editais únicos identificados: {len(unicos)}")

        final = []
        for item in top_10:
            print(f"📖 Lendo título completo de: {item['url']}")
            titulo_real = extrair_titulo_rico(item['url'])
            final.append({
                "edital": titulo_real,
                "documento": item['texto'] if len(item['texto']) > 5 else "Nova Atualização",
                "link_edital": item['url'],
                "data_hora": item['data_txt'],
                "timestamp": item['timestamp']
            })

        os.makedirs('data', exist_ok=True)
        # Salva o JSON
        with open('data/editais.json', 'w', encoding='utf-8') as f:
            json.dump(final, f, ensure_ascii=False, indent=4)
        
        # FORÇA O COMMIT: Salva a hora da última execução
        with open('data/last_run.txt', 'w') as f:
            f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
        print(f"🏁 Finalizado! {len(final)} itens salvos.")
    except Exception as e:
        print(f"🚨 Erro Fatal: {e}")

if __name__ == "__main__":
    run()
