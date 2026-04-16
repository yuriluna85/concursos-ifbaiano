import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timedelta
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
BASE_URL = "https://ifbaiano.edu.br/portal/concursos/"

def formata_data_relativa(dt_obj):
    # O GitHub Actions roda em UTC. Ajustamos para o horário do Brasil (UTC-3)
    agora_br = datetime.utcnow() - timedelta(hours=3)
    hora_min = dt_obj.strftime("%Hh%M")
    
    if dt_obj.date() == agora_br.date():
        return f"Hoje às {hora_min}"
    elif dt_obj.date() == (agora_br - timedelta(days=1)).date():
        return f"Ontem às {hora_min}"
    else:
        return f"{dt_obj.strftime('%d/%m/%Y')} às {hora_min}"

def run():
    print(f"🚀 Iniciando Varredura Ordenada (v2.0.1): {BASE_URL}")
    os.makedirs('data', exist_ok=True)
    
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=30, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        div_concursos = soup.find(id='concursos-e-selecoes') or soup
        
        # Simula a lógica do JS: pega Fixados, Ano Atual e Ano Passado
        agora_br = datetime.utcnow() - timedelta(hours=3)
        ano_atual = str(agora_br.year)
        ano_passado = str(agora_br.year - 1)
        
        ul_fixados = div_concursos.find('ul', class_='fixados')
        ul_atual = div_concursos.find('ul', id=ano_atual)
        ul_passado = div_concursos.find('ul', id=ano_passado)
        
        editais_para_analisar = []
        links_vistos = set()
        
        # Junta os links apenas das listas que importam
        for ul in [ul_fixados, ul_atual, ul_passado]:
            if ul:
                for a in ul.find_all('a', href=True):
                    href = a['href']
                    if href.startswith('https://concurso.ifbaiano.edu.br') and href not in links_vistos:
                        links_vistos.add(href)
                        titulo = a.get_text(separator=' ', strip=True)
                        editais_para_analisar.append({"url": href, "titulo": titulo})

        print(f"📡 Verificando API de {len(editais_para_analisar)} editais estratégicos...")
        
        atualizacoes = []
        
        for edital in editais_para_analisar:
            url_limpa = edital['url'].rstrip('/')
            api_url = f"{url_limpa}/wp-json/wp/v2/media?per_page=15" # Aumentado para garantir que pega documentos
            
            try:
                res_api = requests.get(api_url, headers=HEADERS, timeout=10, verify=False)
                if res_api.status_code == 200:
                    midias = res_api.json()
                    
                    # Filtra apenas documentos (tira imagens) e garante que tem data
                    docs = [m for m in midias if m.get('media_type') != 'image' and 'date' in m]
                    
                    if docs:
                        # ORDENAÇÃO EXPLÍCITA INTERNA (Igual ao JS)
                        docs.sort(key=lambda x: datetime.fromisoformat(x['date']).timestamp(), reverse=True)
                        
                        doc_recente = docs[0]
                        dt_obj = datetime.fromisoformat(doc_recente['date'])
                        
                        atualizacoes.append({
                            "edital": edital['titulo'] if len(edital['titulo']) > 5 else "Edital IF Baiano",
                            "documento": doc_recente['title']['rendered'],
                            "link_edital": edital['url'],
                            "link_doc": doc_recente['source_url'],
                            "dt_obj": dt_obj,
                            "timestamp": dt_obj.timestamp()
                        })
            except Exception:
                pass # Ignora links quebrados da API

        # ORDENAÇÃO GLOBAL: Os 10 arquivos mais recentes de todos
        atualizacoes.sort(key=lambda x: x['timestamp'], reverse=True)
        top_10 = atualizacoes[:10]
        
        resultados_finais = []
        for item in top_10:
            resultados_finais.append({
                "edital": item['edital'],
                "documento": item['documento'],
                "link_edital": item['link_edital'],
                "link_doc": item['link_doc'],
                "data_hora": formata_data_relativa(item['dt_obj']),
                "timestamp": item['timestamp']
            })

        with open('data/editais.json', 'w', encoding='utf-8') as f:
            json.dump(resultados_finais, f, ensure_ascii=False, indent=4)
            
        with open('data/last_run.txt', 'w') as f:
            f.write((datetime.utcnow() - timedelta(hours=3)).strftime("%d/%m/%Y às %H:%M:%S"))
            
        print(f"🏁 Concluído! O Top 10 está estritamente ordenado por data de upload.")

    except Exception as e:
        print(f"🚨 Erro Fatal: {e}")

if __name__ == "__main__":
    run()
