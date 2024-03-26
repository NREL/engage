from pytz import common_timezones
from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
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
        "mapbox_token": True,
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
    user_models = Model_User.objects.filter(user=request.user,
                                            model__is_uploading=False)
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
