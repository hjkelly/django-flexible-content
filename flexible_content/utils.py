from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models import get_model
from django.utils.translation import ugettext as _


def get_app_settings():
    """
    Load the settings and make sure it's not totally wrong.
    """

    app_settings = getattr(settings, 'FLEXIBLE_CONTENT', None)
    if app_settings is None:
        app_settings = {}

    # If the settings were defined as something other than None or a
    # dictionary, raise a stink.
    if not isinstance(app_settings, dict):
        message = _("Setting FLEXIBLE_CONTENT should be a dictionary; "
                    "instead, it was of type {}.".format(type(app_settings)))
        raise ImproperlyConfigured(message)

    return app_settings


def get_model_from_string(model_string):
    """
    Take a list of 'app.ModelName' strings and return a list of model classes.
    """

    # This Django function takes app names and model class names
    # separated by a dot/period.
    model = get_model(*model_string.split('.'))

    # If the model came back as None, it couldn't import it.
    if model is None:
        message = _("Model '{}' was defined in the settings for "
                    "django-flexible-content, but couldn't be loaded. Please "
                    "check your settings file!".format(model_string))
        raise ImportError(message)

    return model


def get_models_from_strings(model_strings):
    """
    Take a list of Python module strings and import those classes.
    """
    models = []

    # Loop through each model string.
    for s in model_strings:
        models.append(get_model_from_string(s))

    return models

