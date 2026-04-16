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
    """Converte 'Hoje às 09h00' ou 'Ontem às 10h00' em datetime real"""
    agora = datetime.now()
    texto_data = texto_data.lower()
    
    # Extrai a hora (ex: 09h23 -> 09:23)
    match_hora = re.search(r'(\d{2})h(\d{2})', texto_data)
    hora, minuto = (match_hora.groups()) if match_hora else (0, 0)
    
    if 'hoje' in texto_data:
        data_base = agora
    elif 'ontem' in texto_data:
        data_base = agora - timedelta(days=1)
    else:
        # Se for data normal DD/MM/AAAA
        match_data = re.search(r'(\d{2}/\d{2}/\d{4})', texto_data)
        if match_data:
            return datetime.strptime(f"{match_data.group(1)} {hora}:{minuto}", "%d/%m/%Y %H:%M")
        return agora # Fallback

    return data_base.replace(hour=int(hora), minute=int(minuto), second=0, microsecond=0)

def extrair_titulo_rico(url):
    """Entra no link para pegar o título completo do edital"""
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Procura o título principal. Geralmente é o H1 ou o primeiro strong no topo
        titulo = soup.find('h1').get_text(strip=True) if soup.find('h1') else ""
        
        # Se o H1 for genérico, tenta pegar o primeiro parágrafo em negrito (comum no IF)
        if "Edital" in titulo and len(titulo) < 20:
            extra = soup.find('strong')
            if extra: titulo = extra.get_text(strip=True)
            
        return titulo if titulo else "Edital de Concurso"
    except:
        return "Edital (Erro ao acessar)"

def run():
    print(f"🚀 Iniciando busca inteligente em: {BASE_URL}")
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        resultados = []

        # Procura os blocos de editais na página inicial
        itens = soup.find_all(['div', 'li', 'tr'], class_=re.compile(r'post|edital|item'))

        for item in itens:
            links = item.find_all('a', href=True)
            texto_todo = item.get_text(separator=' ', strip=True)
            
            # Detecta se há uma data (relativa ou absoluta)
            if any(palavra in texto_todo.lower() for palavra in ['hoje', 'ontem', '/202']):
                link_edital = links[0]['href']
                
                print(f"🔎 Refinando: {link_edital}")
                
                # BUSCA O TÍTULO RICO (Acessando o link)
                titulo_completo = extrair_titulo_rico(link_edital)
                
                # Pega o nome do documento (geralmente o texto do último link)
                nome_doc = links[-1].get_text(strip=True)
                link_doc = links[-1]['href']

                # Processa a data/hora para ordenação
                dt_obj = tratar_data_relativa(texto_todo)

                resultados.append({
                    "edital": titulo_completo,
                    "documento": nome_doc,
                    "link_doc": urljoin(link_edital, link_doc),
                    "link_edital": link_edital,
                    "data_hora": dt_obj.strftime("%d/%m/%Y às %H:%M"),
                    "timestamp": dt_obj.timestamp()
                })

        # Ordenação e salvamento
        resultados.sort(key=lambda x: x['timestamp'], reverse=True)
        os.makedirs('data', exist_ok=True)
        with open('data/editais.json', 'w', encoding='utf-8') as f:
            json.dump(resultados, f, ensure_ascii=False, indent=4)
        
        print(f"🏁 Finalizado! {len(resultados)} editais processados com títulos ricos.")

    except Exception as e:
        print(f"🚨 Erro: {e}")

if __name__ == "__main__":
    run()
