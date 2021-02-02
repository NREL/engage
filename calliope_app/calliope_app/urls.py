"""caliope_api URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import debug_toolbar

from django.contrib import admin
from django.urls import include, path
from django.conf.urls import url
from django.conf import settings
from django.contrib.auth import views as auth_views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static

admin.site.site_header = 'NREL\'s Calliope Admin'

urlpatterns = [
    path('__debug__/', include(debug_toolbar.urls)),
    path('i18n/', include('django.conf.urls.i18n')),
]

urlpatterns += i18n_patterns(
    path('', include('client.urls')),
    path('api/', include('api.urls')),

    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    url(r'^password_reset/$',
        auth_views.PasswordResetView.as_view(
            template_name='registration/pw_reset_form.html',
            email_template_name='registration/pw_reset_email.html',
            subject_template_name='registration/pw_reset_subject.txt',
            from_email=settings.AWS_SES_FROM_EMAIL),
        name='password_reset'),
    url(r'^password_reset/done/$',
        auth_views.PasswordResetDoneView.as_view(
            template_name='registration/pw_reset_done.html'),
        name='password_reset_done'),
    url(r'^reset/\
          (?P<uidb64>[0-9A-Za-z_\-]+)/\
          (?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='registration/pw_reset_confirm.html'),
        name='password_reset_confirm'),
    url(r'^reset/done/$',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='registration/pw_reset_complete.html'),
        name='password_reset_complete'),

    path('admin/', admin.site.urls),
    
    prefix_default_language=True
)

if settings.DEBUG is True:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += staticfiles_urlpatterns()
