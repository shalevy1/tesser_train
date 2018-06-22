"""
you must import this file before using any setting part of django on test
"""
# from django.core.wsgi import get_wsgi_application
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "img_ai_algorithm.settings")
from django.conf import settings
from img_ai_trainer import settings as st
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "img_ai_trainer.settings")
settings.configure(default_settings=st)
from django.apps import AppConfig

BASE_DIR = st.BASE_DIR
