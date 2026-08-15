"""
Configuración de la aplicación leída del entorno (variables de deploy).

Se separa de `constants.py` (que sólo tiene constantes de dominio) porque estos
valores dependen del entorno y algunos son sensibles (credenciales, secretos).
"""
import os

from dotenv import load_dotenv

load_dotenv()

# Credenciales del panel de administración (único usuario, vía variables de entorno).
# ADMIN_PASSWORD es un hash bcrypt del password (no el password en texto plano).
ADMIN_USER     = os.getenv('ADMIN_USER', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', '')

# Configuración JWT
JWT_SECRET           = os.getenv('JWT_SECRET', 'change-me-please')
JWT_ALGORITHM        = 'HS256'
JWT_EXPIRACION_HORAS = int(os.getenv('JWT_EXPIRACION_HORAS', '8'))

# Configuración de Supabase. El backend usa la key service_role (no se expone
# al frontend). En local, ambos valores los imprime `supabase start`.
SUPABASE_URL = os.getenv('SUPABASE_URL', '')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')

# Bucket (privado) donde se guardan las fotos de los docentes. La API sube y
# descarga las imágenes; al frontend se le devuelven como base64 (data URI).
SUPABASE_BUCKET_DOCENTES = os.getenv('SUPABASE_BUCKET_DOCENTES', 'docentes-fotos')

# Orígenes permitidos para CORS (lista separada por comas). Default '*' (todos);
# en producción conviene restringirlo al dominio del frontend.
CORS_ORIGINS = [origen.strip() for origen in os.getenv('CORS_ORIGINS', '*').split(',') if origen.strip()]

# Segundos de cache en el CDN para los GET públicos (Vercel usa s-maxage para
# servir desde el edge sin invocar la función). 0 desactiva el cache.
CACHE_SEGUNDOS = int(os.getenv('CACHE_MAX_AGE', '300'))

# API key para restringir el consumo al frontend (ids-web). Si está vacía, la
# verificación queda deshabilitada (la API es pública). Si tiene valor, todas
# las requests deben enviar el header X-API-Key con ese valor.
API_KEY = os.getenv('API_KEY', '')
