from pytz import common_timezones
from django import forms
from django.contrib.auth import password_validation, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from api.models.engage import User_Profile
from account.validators import email_validator, unicode_email_validator, unicode_chars_validator


class UserRegistrationForm(UserCreationForm):
    """Customized user creation form"""
    email = forms.EmailField(
        label=_("Email"),
        required=True,
        widget=forms.EmailInput,
        validators=(email_validator, unicode_email_validator)
    )
    first_name = forms.CharField(
        label=_("First Name"),
        required=True,
        strip=True,
        validators=(unicode_chars_validator, )
    )
    last_name = forms.CharField(
        label=_("Last Name"),
        required=True,
        strip=True,
        validators=(unicode_chars_validator, )
    )
    organization = forms.CharField(
        label=_("Organization"),
        required=True,
        strip=True,
        validators=(unicode_chars_validator, )
    )
    password1 = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput,
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label=_("Password Confirmation"),
        widget=forms.PasswordInput,
        strip=False,
        help_text=_("Enter the same password as above, for verification."),
    )

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "organization", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data["email"]

        try:
            User.objects.get(email__iexact=email)
            registered = True
        except User.DoesNotExist:
            registered = False

        if registered:
            raise forms.ValidationError("This email already registered, please login with it.")

        return email

    def save(self, host):
        profile = User_Profile.register(
            http_host=host,
            email=self.cleaned_data["email"],
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
            password=self.cleaned_data["password1"],
            organization=self.cleaned_data["organization"]
        )
        return profile.user


class UserAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={'autofocus': True}),
        validators=(email_validator, unicode_email_validator)
    )
    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput,
    )

    error_messages = {
        "invalid_login": _(
            "Please enter a correct %(username)s and password. Note that both "
            "fields may be case-sensitive."
        ),
        "inactive": _("This account is inactive, please activate it with link sent via email, or contact Engage team."),
    }

    def clean(self):
        email = self.cleaned_data.get("username").lower()  # username == email here
        password = self.cleaned_data.get("password")

        if email is not None and password:
            self.user_cache = authenticate(self.request, username=email, password=password)

            if self.user_cache is None:
                # If user is inactive, then it's not allowed to authenticate
                try:
                    user_possible = User.objects.get(username=email)
                    self.confirm_login_allowed(user_possible)
                except ValidationError as e:
                    raise e
                except User.DoesNotExist:
                    pass

                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

    def get_invalid_login_error(self):
        return forms.ValidationError(
            self.error_messages["invalid_login"],
            code="invalid_login",
            params={"username": "email"},
        )

class UserSettingsChangeForm(forms.ModelForm):
    username = forms.CharField(
        label=_("Username"),
        max_length=150,
        required=True
    )
    organization = forms.CharField(
        label=_("Organization"),
        max_length=255,
        required=False,
    )
    timezone = forms.ChoiceField(
        label=_("Time Zone"),
        choices=[(tz, tz) for tz in common_timezones],
        required=True,
    )

    class Meta:
        model = User_Profile
        fields = ('organization', 'timezone')

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        # Handle the case where User_Profile may not exist
        try:
            user_profile = user.user_profile
        except User_Profile.DoesNotExist:
            user_profile = User_Profile(user=user)
            user_profile.save()

        # Pre-fill the form fields with the current data
        self.fields['username'].initial = user.username
        self.fields['organization'].initial = user_profile.organization
        # self.fields['timezone'].initial = user_profile.timezone

    def clean_username(self):
        username = self.cleaned_data['username']
        if username != self.user.username:
            if User.objects.filter(username=username).exists():
                raise ValidationError(_("A user with that username already exists."))
        return username

    def save(self, commit=True):
        # Update the User model
        self.user.username = self.cleaned_data['username']
        self.user.save()

        # Update the User_Profile model
        try:
            profile = self.user.user_profile
        except User_Profile.DoesNotExist:
            profile = User_Profile(user=self.user)

        profile.organization = self.cleaned_data['organization']
        profile.timezone = self.cleaned_data['timezone']
        if commit:
            profile.save()
        return self.user
