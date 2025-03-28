from .settings import *

# Check if running in local development
IS_LOCAL = env.bool('IS_LOCAL', default=False)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG', default=False)

# Add Whitenoise Middleware
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Security settings - adjusted based on environment
SECURE_SSL_REDIRECT = not IS_LOCAL
SECURE_HSTS_SECONDS = 0 if IS_LOCAL else 31536000  # Use 1 year in production
SECURE_HSTS_INCLUDE_SUBDOMAINS = not IS_LOCAL
SECURE_HSTS_PRELOAD = not IS_LOCAL
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = not IS_LOCAL
CSRF_COOKIE_SECURE = not IS_LOCAL
X_FRAME_OPTIONS = 'SAMEORIGIN' if IS_LOCAL else 'DENY'

# Allow hosts based on environment
default_allowed_hosts = ['127.0.0.1', 'localhost'] if IS_LOCAL else []
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=default_allowed_hosts)

# Static files configuration
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Use appropriate static files storage based on environment
STATICFILES_STORAGE = (
    'django.contrib.staticfiles.storage.StaticFilesStorage'
    if IS_LOCAL else
    'whitenoise.storage.CompressedManifestStaticFilesStorage'
)

# Ensure static directory exists
os.makedirs(os.path.join(BASE_DIR, 'static'), exist_ok=True)
os.makedirs(STATIC_ROOT, exist_ok=True)

# Email configuration (replace with your email service settings)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env('EMAIL_PORT', default=587)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@yourdomain.com')

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': env('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
    },
}

# Cache configuration (using Redis with fallback)
try:
    import redis
    from django_redis.cache import RedisCache
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': env('REDIS_URL', default='redis://127.0.0.1:6379/1'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    }
    # Test Redis connection
    redis_client = redis.from_url(env('REDIS_URL', default='redis://127.0.0.1:6379/1'))
    redis_client.ping()
    
    # Session configuration (using Redis)
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'default'
except (ImportError, redis.ConnectionError):
    # Fallback to local memory cache if Redis is not available
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }
    # Fallback to database sessions
    SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Celery configuration with fallback
try:
    CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://127.0.0.1:6379/0')
    CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://127.0.0.1:6379/0')
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
except:
    # If Redis is not available, disable Celery functionality
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True

# Django allauth settings
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_LOGIN_ATTEMPTS_LIMIT = 5
ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT = 300  # 5 minutes

# Set this to True if you're using HTTPS
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True 