from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls import url
from django.urls import path

from template import views

urlpatterns = [
    path('<model_uuid>/templates/',
         views.templates_view,
         name='templates')
]


