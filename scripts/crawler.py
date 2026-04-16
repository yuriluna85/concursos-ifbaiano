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
    """Imita a função comparaData e formataHora do seu JS original"""
    agora = datetime.now()
    hora_min = dt_obj.strftime("%Hh%M")
    
    # Verifica se é hoje ou ontem
    if dt_obj.date() == agora.date():
        return f"Hoje às {hora_min}"
    elif dt_obj.date() == (agora - timedelta(days=1)).date():
        return f"Ontem às {hora_min}"
    else:
        # Formato: 14/04/2026 às 15h30
        return f"{dt_obj.strftime('%d/%m/%Y')} às {hora_min}"

def run():
    print(f"🚀 Iniciando Varredura via WP API: {BASE_URL}")
    os.makedirs('data', exist_ok=True)
    
    try:
        # 1. Pega a página principal para descobrir os links dos editais
        response = requests.get(BASE_URL, headers=HEADERS, timeout=30, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Procura a div principal que o seu JS usa (#concursos-e-selecoes)
        div_concursos = soup.find(id='concursos-e-selecoes') or soup
        
        links_vistos = set()
        editais_para_analisar = []
        
        # Pega as primeiras 40 URLs válidas (Fixados + Ano Atual garantidos)
        for a in div_concursos.find_all('a', href=True):
            href = a['href']
            if href.startswith('https://concurso.ifbaiano.edu.br') and href not in links_vistos:
                links_vistos.add(href)
                # O texto do link é o nome oficial do Edital!
                titulo = a.get_text(separator=' ', strip=True)
                editais_para_analisar.append({"url": href, "titulo": titulo})
                if len(editais_para_analisar) >= 40: break

        print(f"📡 Lendo banco de dados (WP-JSON) de {len(editais_para_analisar)} editais...")
        
        atualizacoes = []
        
        # 2. Faz exatamente o que o JavaScript faz: Acessa a API de Mídia
        for edital in editais_para_analisar:
            url_limpa = edital['url'].rstrip('/')
            # per_page=5 para ser super rápido, só queremos a última mídia
            api_url = f"{url_limpa}/wp-json/wp/v2/media?per_page=5"
            
            try:
                # Consulta a API do WordPress do edital específico
                res_api = requests.get(api_url, headers=HEADERS, timeout=10, verify=False)
                if res_api.status_code == 200:
                    midias = res_api.json()
                    
                    # Filtra: item.media_type !== 'image'
                    docs = [m for m in midias if m.get('media_type') != 'image']
                    
                    if docs:
                        # docs[0] já é o mais recente porque a API do WP ordena por data desc
                        doc_recente = docs[0]
                        
                        # Extrai a data ISO do WordPress (ex: "2026-04-16T14:09:00")
                        dt_obj = datetime.fromisoformat(doc_recente['date'])
                        nome_arquivo = doc_recente['title']['rendered']
                        link_arquivo = doc_recente['source_url']
                        
                        atualizacoes.append({
                            "edital": edital['titulo'] if len(edital['titulo']) > 5 else "Edital IF Baiano",
                            "documento": nome_arquivo,
                            "link_edital": edital['url'],
                            "link_doc": link_arquivo, # Temos o link direto do PDF!
                            "dt_obj": dt_obj,
                            "timestamp": dt_obj.timestamp()
                        })
            except Exception as api_err:
                pass # Ignora se a API de um edital antigo falhar

        # 3. Ordena os dados globais pelo timestamp mais recente
        atualizacoes.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # 4. Filtra os 10 mais recentes
        top_10 = atualizacoes[:10]
        
        # Formata os dados para o JSON final
        resultados_finais = []
        for item in top_10:
            resultados_finais.append({
                "edital": item['edital'],
                "documento": item['documento'],
                "link_edital": item['link_edital'],
                "link_doc": item['link_doc'], # Novo campo com o link direto
                "data_hora": formata_data_relativa(item['dt_obj']),
                "timestamp": item['timestamp']
            })

        # 5. Salva no repositório
        with open('data/editais.json', 'w', encoding='utf-8') as f:
            json.dump(resultados_finais, f, ensure_ascii=False, indent=4)
            
        with open('data/last_run.txt', 'w') as f:
            f.write(datetime.now().strftime("%d/%m/%Y às %H:%M:%S"))
            
        print(f"🏁 Concluído! O Top 10 foi atualizado usando o banco WP.")

    except Exception as e:
        print(f"🚨 Erro Fatal na estrutura principal: {e}")

if __name__ == "__main__":
    run()
