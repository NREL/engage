from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls import url
from django.urls import path

from template import views
from template import geophires

urlpatterns = [
    path('model/templates/',
        views.model_templates,
         name='templates'),
    path('model/templates/create/',
          views.add_template,
          name='add_template'),
    path('geophires/',
          geophires.request_geophires,
          name='request_geophires')
]