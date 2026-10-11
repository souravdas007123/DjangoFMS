from django.apps import AppConfig


class UiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ui"
    verbose_name = "FactoryOS UI"

    def ready(self):
        # The built-in Django admin stays available for superusers (user/group
        # management and emergency edits); label it so nobody mistakes it for the app.
        from django.contrib import admin

        admin.site.site_header = "FactoryOS · Admin (backup)"
        admin.site.site_title = "FactoryOS Admin"
        admin.site.index_title = "Superuser tools"
