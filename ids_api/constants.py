from datetime import date

# URL base de la API
BASE_URL = '/ids_api'

# Rol del único usuario de administración (viaja dentro del JWT)
ROL_ADMIN = 'admin'

# Roles permitidos para los docentes
ROLES_DOCENTE = ('Profesor', 'Ayudante', 'Colaborador')

# Tipos de clase válidos para el cronograma
TIPOS_CLASE = ('Presencial', 'Virtual', 'Feriado', 'Sin clases')

# Período de clases del cuatrimestre. Definen la cantidad de semanas y, por lo
# tanto, la cantidad de clases (2 por semana: lunes y miércoles).
INICIO_CLASES = date(2026, 8, 17)   # lunes de la primera semana de clases
FIN_CLASES    = date(2026, 11, 30)  # lunes de la última semana de clases
DIAS_CLASE    = (0, 2)              # weekday(): lunes=0, miércoles=2

# Defaults para las clases autogeneradas (fechas del período que no se cargaron)
TIPO_CLASE_DEFAULT   = 'Virtual'
TITULO_CLASE_DEFAULT = 'A definir'

# Formato de fecha ISO (YYYY-MM-DD) usado internamente y en el JSON de la API
FECHA_ISO_FORMATO = '%Y-%m-%d'

# Restricciones de las fotos de docentes (la config del bucket vive en config.py)
EXTENSIONES_IMAGEN = ('png', 'jpg', 'jpeg', 'gif', 'webp')
MAXIMO_IMAGEN_MB = 5

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
ERROR_CODE_API_KEY_INVALIDA    = 'api.key.invalid'
ERROR_CODE_RATE_LIMIT          = 'rate.limit.exceeded'
ERROR_CODE_TOKEN_FALTANTE      = 'auth.token.missing'
ERROR_CODE_TOKEN_INVALIDO      = 'auth.token.invalid'
ERROR_CODE_TOKEN_EXPIRADO      = 'auth.token.expired'
ERROR_CODE_SIN_PERMISO         = 'auth.forbidden'
ERROR_CODE_DOCENTE_NOT_FOUND   = 'docente.not.found'
ERROR_CODE_EMAIL_DUPLICADO     = 'email.duplicated'
ERROR_CODE_CLASE_NOT_FOUND     = 'clase.not.found'
ERROR_CODE_ARCHIVO_FALTANTE    = 'file.missing'
ERROR_CODE_CSV_INVALIDO        = 'invalid.csv'
ERROR_CODE_FECHA_DUPLICADA     = 'fecha.duplicated'
ERROR_CODE_CRONOGRAMA_NO_VACIO = 'cronograma.not.empty'
ERROR_CODE_FECHA_DIA_INVALIDO  = 'fecha.invalid.weekday'
ERROR_CODE_FECHA_FUERA_PERIODO = 'fecha.out.of.period'
ERROR_CODE_SEMANA_INCORRECTA   = 'semana.mismatch'
