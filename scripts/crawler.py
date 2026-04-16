import requests
from bs4 import BeautifulSoup
import json
import re
import os
from datetime import datetime, timedelta
from urllib.parse import urljoin
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}

BASE_URL = "https://ifbaiano.edu.br/portal/concursos/"

def tratar_data_relativa(texto):
    agora = datetime.now()
    texto = texto.lower()
    match_hora = re.search(r'(\d{1,2})h(\d{2})', texto)
    h, m = (int(match_hora.group(1)), int(match_hora.group(2))) if match_hora else (0, 0)
    
    if 'hoje' in texto:
        dt = agora
    elif 'ontem' in texto:
        dt = agora - timedelta(days=1)
    else:
        match_data = re.search(r'(\d{2}/\d{2}/\d{4})', texto)
        if match_data:
            try: return datetime.strptime(f"{match_data.group(1)} {h}:{m}", "%d/%m/%Y %H:%M")
            except: return agora
        return agora
    return dt.replace(hour=h, minute=m, second=0, microsecond=0)

def extrair_titulo_detalhado(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=15, verify=False)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        # Procura o título principal no H1 ou no primeiro strong do conteúdo
        alvo = soup.find('h1') or soup.find('strong')
        if alvo:
            txt = alvo.get_text(strip=True)
            return txt if len(txt) > 10 else "Edital Institucional"
        return "Edital IF Baiano"
    except:
        return "Edital (Ver no Portal)"

def run():
    print(f"🚀 Varrendo Portal: {BASE_URL}")
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=30, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Dicionário para garantir apenas UM card por URL de edital
        mapa_editais = {}

        # O portal WordPress do IF usa 'article' para cada item da lista
        blocos = soup.find_all(['article', 'div'], class_=re.compile(r'post|item|edital'))

        for bloco in blocos:
            link_tag = bloco.find('a', href=True)
            if not link_tag: continue
            
            url_edital = urljoin(BASE_URL, link_tag['href'])
            if 'concurso.ifbaiano.edu.br/portal/' not in url_edital: continue

            # Se já processamos este edital neste loop, pulamos
            if url_edital in mapa_editais: continue

            texto_bloco = bloco.get_text(separator=' ', strip=True)
            
            # Tenta pegar o nome do último arquivo (geralmente em negrito ou no final do texto)
            # Se não achar nada específico, tenta pegar o texto que vem depois da hora
            partes = texto_todo = bloco.get_text(separator='|', strip=True).split('|')
            nome_documento = partes[-1] if len(partes) > 1 else "Clique para ver arquivos"
            
            print(f"🔎 Processando: {url_edital}")
            titulo_rico = extrair_titulo_detalhado(url_edital)
            dt_obj = tratar_data_relativa(texto_bloco)

            mapa_editais[url_edital] = {
                "edital": titulo_rico,
                "documento": nome_documento if len(nome_documento) > 5 else "Nova atualização disponível",
                "link_edital": url_edital,
                "data_hora": dt_obj.strftime("%d/%m/%Y às %H:%M"),
                "timestamp": dt_obj.timestamp()
            }

        resultados = list(mapa_editais.values())
        resultados.sort(key=lambda x: x['timestamp'], reverse=True)

        os.makedirs('data', exist_ok=True)
        with open('data/editais.json', 'w', encoding='utf-8') as f:
            json.dump(resultados, f, ensure_ascii=False, indent=4)
        print(f"🏁 {len(resultados)} editais únicos salvos.")
    except Exception as e:
        print(f"🚨 Erro: {e}")

if __name__ == "__main__":
    run()
