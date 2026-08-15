import logging

# Usar el almacén de certificados del sistema operativo para verificar TLS.
# Necesario en entornos con inspección SSL corporativa (root CA propio en la
# cadena). Debe ejecutarse antes de crear el cliente de Supabase (httpx).
import truststore
truststore.inject_into_ssl()

from flask import Flask, request, jsonify
from flask_cors import CORS

from ids_api.constants import BASE_URL, ERROR_CODE_API_KEY_INVALIDA
from ids_api.config import CORS_ORIGINS, API_KEY
from ids_api.utils import construir_error_api
from ids_api.routes.auth import auth_bp
from ids_api.routes.docentes import docentes_bp
from ids_api.routes.cronograma import cronograma_bp

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(name)s - %(message)s')

app = Flask(__name__)
app.json.sort_keys = False

# Habilitar CORS para que el frontend (ids-web) pueda consumir la API.
# Los orígenes permitidos se configuran con CORS_ORIGINS (default: todos).
CORS(app, origins=CORS_ORIGINS)


@app.before_request
def validar_api_key():
    """
    Restringe el consumo al frontend: exige el header X-API-Key.

    Solo se aplica si API_KEY está configurada (si no, la API es pública). Los
    preflight CORS (OPTIONS) se dejan pasar. En caché de CDN (cache hit) este
    hook no corre, así que los GET cacheados siguen sirviéndose desde el edge.
    """
    if not API_KEY or request.method == 'OPTIONS':
        return None

    if request.headers.get('X-API-Key') != API_KEY:
        return jsonify(construir_error_api(
            code=ERROR_CODE_API_KEY_INVALIDA,
            message='API key inválida o faltante',
            description='Debe enviarse el header X-API-Key con una clave válida.'
        )), 401

    return None


app.register_blueprint(auth_bp, url_prefix=BASE_URL)
app.register_blueprint(docentes_bp, url_prefix=BASE_URL)
app.register_blueprint(cronograma_bp, url_prefix=BASE_URL)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
