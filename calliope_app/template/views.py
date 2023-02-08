from pytz import common_timezones

from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from template import Help_Guide
from api.models.configuration import Model, Model_User
from template.models import Template

@login_required
def templates_view(request):
    """
    View the "Templates" page

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
    template_models = Template.objects

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
        "template_models": template_models
    }

    return render(request, "templates/templates.html", context)
