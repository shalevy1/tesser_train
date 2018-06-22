from django.apps import AppConfig


class ImgAiTrainerConfig(AppConfig):
    name = 'img_ai_trainer'

    def ready(self):
        import logging
        logger = logging.getLogger('django_logger')
        print("just test logger!")