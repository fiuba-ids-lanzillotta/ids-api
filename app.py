import logging

# Usar el almacén de certificados del sistema operativo para verificar TLS.
# Necesario en entornos con inspección SSL corporativa (root CA propio en la
# cadena). Debe ejecutarse antes de crear el cliente de Supabase (httpx).
import truststore
truststore.inject_into_ssl()

from flask import Flask
from flask_cors import CORS

from ids_api.constants import BASE_URL
from ids_api.routes.auth import auth_bp
from ids_api.routes.docentes import docentes_bp
from ids_api.routes.cronograma import cronograma_bp

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(name)s - %(message)s')

app = Flask(__name__)
app.json.sort_keys = False

# Habilitar CORS para que el frontend (ids-web) pueda consumir la API
CORS(app)

app.register_blueprint(auth_bp, url_prefix=BASE_URL)
app.register_blueprint(docentes_bp, url_prefix=BASE_URL)
app.register_blueprint(cronograma_bp, url_prefix=BASE_URL)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
