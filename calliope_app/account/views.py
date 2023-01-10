import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AdminPasswordChangeForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect

from account.forms import UserRegistrationForm, UserAuthenticationForm
from api.models.engage import User_Profile


def user_registration(request):
    """
    User registration view
    """
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save(host=request.META["HTTP_HOST"])
            email = form.cleaned_data["email"]
            messages.success(
                request,
                f"Registration successful, activation link was sent to your email address - {email}"
            )
            return redirect("login")
        messages.error(request, "Unsuccessful registration. Invalid information.")
    else:
        form = UserRegistrationForm()
    
    template_name = "registration/registration.html"
    return render(request, template_name, context={"registration_form": form})


@csrf_protect
def user_activation(request, activation_uuid):
    """
    Activate a newly registered user. This link will be sent to the user's
    email upon self-registration.

    Parameters:
    activation_uuid (uuid): required

    Returns: HttpResponse Redirect to Login page

    Example:
    GET: /api/user_activation/
    """

    try:
        User_Profile.activate(activation_uuid)
        url = "%s?status=active" % reverse('login')
    except Exception as e:
        print('User Activation Error: {}'.format(e))
        url = reverse('login')
    return HttpResponseRedirect(url)


def user_login(request):
    """
    User authentication view
    """
    redirect_url = request.GET.get("next", settings.LOGIN_REDIRECT_URL)
    if not redirect_url:
        redirect_url = "/"
    
    if request.method == "POST":
        form = UserAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.user_cache
            if user is not None:
                login(request, user)
                return redirect(redirect_url)
        
        messages.error(request, form.non_field_errors())
    
    form = UserAuthenticationForm()

    return render(request, "registration/login.html", context={"login_form": form})


@login_required
def password_view(request):
    """
    View the "Password Manager" page

    Parameters:
    model_uuid (uuid): required

    Returns: HttpResponse

    Example:
    http://0.0.0.0:8000/settings/password/
    """

    user = request.user
    if user.has_usable_password():
        PasswordForm = PasswordChangeForm
    else:
        PasswordForm = AdminPasswordChangeForm

    if request.method == 'POST':
        form = PasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            messages.success(request,
                             "Your password was successfully updated!")
            return redirect('password')
        else:
            messages.error(request, 'Please correct the error below')
    else:
        form = PasswordForm(user)

    context = {
        'user': user,
        'form': form,
    }

    return render(request, "password.html", context)


@csrf_protect
def set_timezone(request):
    """
    Set a user's timezone.

    Parameters:
    language (str): required

    Returns: HttpResponse

    Example:
    POST: /api/set_timezone/
    """

    user = request.user
    timezone = request.POST["timezone"]
    next_url = request.POST.get('next', '/')

    profile = User_Profile.objects.get(user=user)
    profile.timezone = timezone
    profile.save()

    return HttpResponseRedirect(next_url)
