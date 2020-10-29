Language Translation
====================

This project supports internationalization (i18n) and localization (l10n), the default language is English. 
To add a new language, please update Django settings, the code snippts below shows how to support Spanish.

.. code-block:: python

    LANGUAGES = [
        ('en', gettext('English')),
        ('es', gettext('Spanish')),
        # Add new langugage here
    ]

We use Django package ``modeltranslation`` to translate dynamic content of existing models to other languages.

.. code-block:: python

    # MODELTRANSLATION
    MODELTRANSLATION_LANGUAGES = ('en', 'es') # Add new language here.

For detailed usage, please refer to https://django-modeltranslation.readthedocs.io/en/latest/.

Next, it takes three steps to finish the translation for localization.

1. Create po file for the newly added language in locale folder, for example

.. code-block:: bash

    python manage.py makemessages -l es

2. Translate the messages in the po file, for example

.. code-block:: 

    #: client/templates/registration/login.html:65
    msgid "Login"
    msgstr "Iniciar sesión"

3. Compile translated messages into mo files for use with the built-in gettext support.

.. code-block::

    python manage.py makemessages -l es
