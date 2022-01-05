from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import EmailValidator, RegexValidator, slug_unicode_re
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _


unicode_chars_validator = RegexValidator(
    slug_unicode_re,
    _("Enter a valid string consisting of unicode letters, numbers, underscores or hyphens."),
    "invalid"
)

email_validator = EmailValidator()

@deconstructible
class UnicodeEmailValidator(UnicodeUsernameValidator):
    regex = r"^[\w.@+-]+$"
    message = _(
        "Enter a valid email consisting of letters, numbers, and @/./+/-/_ characters."
    )
    flags = 0

unicode_email_validator = UnicodeEmailValidator()
