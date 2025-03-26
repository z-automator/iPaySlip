"""
WSGI config for production deployment.
"""

import os
from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'payslip.settings_prod')

application = get_wsgi_application()
application = WhiteNoise(application) 