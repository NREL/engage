from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls import url
from django.urls import path

from template import views

urlpatterns = [
    path('templates/model/',
         views.templates_admin_view,
         name='templates_admin'),
    path('templates/model/create/',
         views.add_template,
         name='add_template')
]