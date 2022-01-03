import json

from django.contrib import messages
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AdminPasswordChangeForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect

from account.models import User_Profile
from api.models.configuration import Model


@csrf_protect
def user_registration(request):
    """
    Submit a user's registration, triggers a link sent to the user's email
    to activate their account.

    Parameters:
    first_name (string): required
    last_name (string): required
    organization (string): required
    email (string): required
    password (string): required

    Returns (json): Action Confirmation

    Example:
    POST: /api/user_registration/
    """

    first_name = request.POST.get('first_name').title()
    last_name = request.POST.get('last_name').title()
    organization = request.POST.get('organization')
    email = request.POST.get('email').lower()
    password = request.POST.get('password')

    if any((c in ['<','>','{','}','|']) for c in email):
        payload = {"message":'Invalid email'}
        return HttpResponse(json.dumps(payload, indent=4),
                        content_type="application/json")
    if any((c in ['<','>','{','}','|']) for c in first_name):
        payload = {"message":'Invalid name'}
        return HttpResponse(json.dumps(payload, indent=4),
                        content_type="application/json")
    if any((c in ['<','>','{','}','|']) for c in last_name):
        payload = {"message":'Invalid name'}
        return HttpResponse(json.dumps(payload, indent=4),
                        content_type="application/json")
    if any((c in ['<','>','{','}','|']) for c in organization):
        payload = {"message":'Invalid org'}
        return HttpResponse(json.dumps(payload, indent=4),
                        content_type="application/json")
    User_Profile.register(http_host=request.META['HTTP_HOST'],
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        password=password,
                        organization=organization)

    payload = {"message": ("Thank you! A verification email has been sent!"
                        "\nTo complete your registration, you must click"
                        " on the activation link sent to {}".format(email))}

    return HttpResponse(json.dumps(payload), content_type="application/json")


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
