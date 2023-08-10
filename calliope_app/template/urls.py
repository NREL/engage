from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls import url
from django.urls import path

from template import views
from template import geophires

urlpatterns = [
    path('model/templates/', views.model_templates, name='templates'),
    path('model/templates/create/', views.add_template, name='add_template'),
    path('model/templates/delete/', views.delete_template, name='delete_template'),
    path('geophires/', geophires.geophires_request, name='geophires_request'),
    path('geophires/status/', geophires.geophires_request_status, name='geophires_request_status'),
    path('geophires/response/', geophires.geophires_response, name='geophires_response'),
    path('geophires/outputs/', geophires.geophires_outputs, name='geophires_outputs'),
    path('geophires/plotting/', geophires.geophires_plotting, name='geophires_plotting'),
]
