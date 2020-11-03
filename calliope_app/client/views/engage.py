import os
from pytz import common_timezones

from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.urls import reverse

from api.models.engage import Help_Guide
from api.models.configuration import Model, Model_User


@login_required
def home_view(request):
    """
    View the "Home" page

    Returns: HttpResponse

    Example:
    http://0.0.0.0:8000/
    """

    user_models = Model_User.objects.filter(
        user=request.user,
        model__snapshot_version=None,
        model__public=False).order_by('-last_access')
    model_ids = user_models.values_list(
        "model_id", flat=True)
    snapshots = Model.objects.filter(
        snapshot_base_id__in=model_ids)
    public_models = Model.objects.filter(
        snapshot_version=None,
        public=True)
    user_models = list(user_models)

    if len(user_models) > 0:
        last_model = user_models[0].model
    elif len(public_models) > 0:
        last_model = public_models[0]
    else:
        last_model = None

    context = {
        "timezones": common_timezones,
        "last_model": last_model,
        "user_models": user_models,
        "public_models": public_models,
        "snapshots": snapshots,
        "mapbox_token": settings.MAPBOX_TOKEN,
        "help_content": Help_Guide.get_safe_html('home'),
    }

    return render(request, "home.html", context)


@login_required
def share_view(request):
    """
    View the "Model Sharing" page

    Parameters:
    model_uuid (uuid): required

    Returns: HttpResponse

    Example:
    http://0.0.0.0:8000/share/
    """

    selected_model_uuid = request.GET.get('model_uuid', None)
    user_models = Model_User.objects.filter(user=request.user)
    users = User.objects.all().exclude(
        id=request.user.id).order_by('last_name', 'first_name')

    context = {
        "timezones": common_timezones,
        "user": request.user,
        "users": users,
        "user_models": user_models,
        "selected_model_uuid": str(selected_model_uuid),
        "help_content": Help_Guide.get_safe_html('share'),
    }
    return render(request, "share.html", context)


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


@login_required
def admin_login_view(request):
    """
    Redirect to login view

    Parameters:
    model_uuid (uuid): required

    Returns: HttpResponse

    Example:
    http://0.0.0.0:8000/share/
    """
    context = {}
    return render(request, "share.html", context)


def user_login(request):
    """
    View the "Login" page

    Returns: HttpResponse

    Example:
    http://0.0.0.0:8000/login/
    """
    redirect_to = request.GET.get('next', '')
    status = request.GET.get('status', 'login')
    status_messages = {'active': ("Account has been activated!\n"
                                  "Please proceed to login..."),
                       'inactive': ("Account has not yet been activated!\n"
                                    "Email must be verified first..."),
                       'invalid-email': ("Email is invalid!\n"
                                         "Please try again..."),
                       'invalid-password': ("Password is invalid!\n"
                                            "Please try again...")}

    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('home'))
    if request.method == 'POST':
        email = request.POST.get('email').lower()
        password = request.POST.get('password')

        user = User.objects.filter(username=email).first()
        if user:
            if not user.is_active:
                url = "%s?status=inactive" % reverse('login')
                return HttpResponseRedirect(url)
            else:
                user = authenticate(username=email, password=password)
                if user:
                    login(request, user)
                    if redirect_to:
                        return HttpResponseRedirect(redirect_to)
                    else:
                        return HttpResponseRedirect(reverse('home'))
                else:
                    url = "%s?status=invalid-password" % reverse('login')
                    return HttpResponseRedirect(url)

        else:
            url = "%s?status=invalid-email" % reverse('login')
            return HttpResponseRedirect(url)
    else:
        public_models = Model.objects.filter(
            snapshot_version=None,
            public=True)
        context = {'redirect_to': redirect_to,
                   'status': status_messages.get(status, ''),
                   'public_models': public_models}
        return render(request, 'registration/login.html', context)
