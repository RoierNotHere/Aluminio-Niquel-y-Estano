from http.server import BaseHTTPRequestHandler
import cloudscraper
from bs4 import BeautifulSoup
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Mapeo de minerales con sus símbolos y URLs alternativas
        minerales_target = {
            'Níquel': {'symbol': 'LN1:COM', 'href': '/commodity/nickel'},
            'Aluminio': {'symbol': 'LMAAH:COM', 'href': '/commodity/aluminum'},
            'Estaño': {'symbol': 'LMSN:COM', 'href': '/commodity/tin'}
        }
        resultados = {}
        
        try:
            scraper = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'desktop': True
                }
            )
            
            url = "https://tradingeconomics.com/commodities"
            res = scraper.get(url, timeout=10)
            
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                
                for nombre, info in minerales_target.items():
                    try:
                        # Buscamos primero por atributo data-symbol
                        fila = soup.find('tr', {'data-symbol': info['symbol']})
                        
                        # Fallback por URL si el símbolo cambia en el HTML
                        if not fila:
                            enlace = soup.find('a', href=lambda h: h and info['href'] in h)
                            if enlace:
                                fila = enlace.find_parent('tr')

                        if fila:
                            precio_raw = fila.find('td', id='p')
                            resultados[nombre] = precio_raw.text.strip() if precio_raw else "N/A"
                        else:
                            resultados[nombre] = "No encontrado"
                    except Exception:
                        resultados[nombre] = "Error al procesar"
                
                payload = {
                    "datos": resultados,
                    "status": "success"
                }
                status_code = 200
            else:
                payload = {"error": f"Error del sitio origen: {res.status_code}"}
                status_code = 502

        except Exception as e:
            payload = {"error": str(e)}
            status_code = 500

        # Respuesta JSON para Vercel
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode('utf-8'))
        return
