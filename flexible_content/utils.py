from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models import get_model

def get_app_settings():
    """
    Load the settings and make sure it's not totally wrong.
    """

    app_settings = getattr(settings, 'IPANEMA', None)
    if app_settings is None:
        app_settings = {}

    # If the settings were defined as something other than None or a 
    # dictionary, raise a stink.
    if not isinstance(app_settings, dict):
        problem = ("Setting IPANEMA should be a dictionary; instead, it was "
                   "of type {}.".format(type(app_settings)))
        raise ImproperlyConfigured(problem)

    return app_settings

def get_model_from_string(model_string):
    """
    Take Python module path string and import that model.
    """

    # Split the string by dots.
    path_parts = model_string.split('.')
    # Pull off the class name, which we'll need later.
    class_name = path_parts.pop()

    # Import the module the class resides in.
    try:
        module_string = '.'.join(path_parts)
        module = __import__(module_string)
    # If it couldn't be imported, fail with a more helpful message.
    except ImportError:
        raise ImportError("The settings file specified a content item class "
                          "called {}, but module {} couldn't be imported ".
                          format(model_string, module_string))
    # From that module, pull and return the class they asked for.
    try:
        cls = getattr(module, class_name)
    # If it couldn't be imported, fail with a more helpful message.
    except AttributeError:
        raise ImportError("The settings file specified a content item class "
                          "called {}, but module {} didn't contain a class by "
                          "that name.".format(model_string, module_string))

    return cls

def get_models_from_strings(model_strings):
    """
    Take a list of Python module strings and import those classes.
    """
    models = []

    # Loop through each model string.
    for s in model_strings:
        models.append(get_model_from_string(s))

    return models

