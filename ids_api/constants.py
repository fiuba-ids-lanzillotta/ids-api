import os
from dotenv import load_dotenv

load_dotenv()

# URL base de la API
BASE_URL = '/ids_api'

# Rol del único usuario de administración (viaja dentro del JWT)
ROL_ADMIN = 'admin'

# Roles permitidos para los docentes
ROLES_DOCENTE = ('Profesor', 'Ayudante', 'Colaborador')

# Tipos de clase válidos para el cronograma
TIPOS_CLASE = ('Presencial', 'Virtual', 'Feriado', 'Sin clases')

# Credenciales del panel de administración (único usuario, vía variables de entorno).
# ADMIN_PASSWORD es un hash bcrypt del password (no el password en texto plano).
ADMIN_USER     = os.getenv('ADMIN_USER', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', '')

# Configuración JWT
JWT_SECRET     = os.getenv('JWT_SECRET', 'change-me-please')
JWT_ALGORITHM  = 'HS256'
JWT_EXP_HORAS  = int(os.getenv('JWT_EXP_HORAS', '8'))

# Configuración de Supabase. El backend usa la key service_role (no se expone
# al frontend). En local, ambos valores los imprime `supabase start`.
SUPABASE_URL = os.getenv('SUPABASE_URL', '')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')

# Bucket (privado) donde se guardan las fotos de los docentes. La API sube y
# descarga las imágenes; al frontend se le devuelven como base64 (data URI).
SUPABASE_BUCKET_DOCENTES = os.getenv('SUPABASE_BUCKET_DOCENTES', 'docentes-fotos')
EXTENSIONES_IMAGEN = ('png', 'jpg', 'jpeg', 'gif', 'webp')
MAX_IMAGEN_MB = 5

# Códigos de error
ERROR_CODE_INVALID_BODY        = 'invalid.body'
ERROR_CODE_INVALID_MIN_VALUE   = 'invalid.min.value'
ERROR_CODE_INVALID_MAX_VALUE   = 'invalid.max.value'
ERROR_CODE_INVALID_EMAIL       = 'invalid.email.format'
ERROR_CODE_INVALID_ROL_DOCENTE = 'invalid.rol.docente'
ERROR_CODE_INVALID_IMAGEN      = 'invalid.imagen'
ERROR_CODE_IMAGEN_UPLOAD       = 'imagen.upload.failed'
ERROR_CODE_INVALID_TIPO_CLASE  = 'invalid.tipo.clase'
ERROR_CODE_CREDENCIALES        = 'invalid.credentials'
ERROR_CODE_TOKEN_FALTANTE      = 'auth.token.missing'
ERROR_CODE_TOKEN_INVALIDO      = 'auth.token.invalid'
ERROR_CODE_TOKEN_EXPIRADO      = 'auth.token.expired'
ERROR_CODE_SIN_PERMISO         = 'auth.forbidden'
ERROR_CODE_DOCENTE_NOT_FOUND   = 'docente.not.found'
ERROR_CODE_CLASE_NOT_FOUND     = 'clase.not.found'
ERROR_CODE_ARCHIVO_FALTANTE    = 'file.missing'
ERROR_CODE_CSV_INVALIDO        = 'invalid.csv'
ERROR_CODE_FECHA_DUPLICADA     = 'fecha.duplicated'
ERROR_CODE_CRONOGRAMA_NO_VACIO = 'cronograma.not.empty'
