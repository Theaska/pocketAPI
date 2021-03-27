from .settings import *

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'helpers.jwt_helper.authentication.JWTAuthentication',
    ],
    'DEFAULT_FILTER_BACKENDS': ['helpers.filters.CustomFilterBackend'],
    'NON_FIELD_ERRORS_KEY': 'errors',
}
AUTH_HEADER_NAME = 'Access-Token'

# Swagger
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': AUTH_HEADER_NAME,
            'in': 'header',
            'authorizationUrl': 'accounts:login',
            'tokenUrl': 'accounts:token',
        }
    },
    'PERSIST_AUTH': True
}
