from django.views.decorators.csrf import csrf_protect
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404

from api.models.engage import User_Profile
from api.tasks import upgrade_066

import json


# ------ Users ------


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
def apply_upgrade_066(request):
    """
    Launch data migration to Calliope 066.

    Parameters:

    Returns (json): Action Confirmation

    Example:
    POST: /api/upgrade_066/
    """

    payload = {}
    if request.user.is_staff:
        async_result = upgrade_066.apply_async()
        payload['task_id'] = async_result.id
    else:
        payload['message'] = "Not authorized!"

    return HttpResponse(json.dumps(payload), content_type="application/json")
