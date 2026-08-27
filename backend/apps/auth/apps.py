from django.apps import AppConfig


class AuthnConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.auth'
    # 'auth' colidiria com o label de django.contrib.auth; usamos 'authn'.
    label = 'authn'
    verbose_name = 'Autenticação'
