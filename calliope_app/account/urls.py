from django.contrib.auth import views as auth_views
from django.conf import settings
from django.urls import re_path
from django.urls import path

from account import views


urlpatterns = [
    path('login/', views.user_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.user_registration, name='register'),

    path(
        'settings/password/',
        views.password_view,
        name='password'
    ),
    path(
        'user_activation/<activation_uuid>',
        views.user_activation,
        name='user_activation'
    ),
    path(
        'set_timezone/',
        views.set_timezone,
        name='set_timezone'
    ),

    re_path(
        r'^password_reset/$',
        auth_views.PasswordResetView.as_view(
            template_name='registration/pw_reset_form.html',
            email_template_name='registration/pw_reset_email.html',
            subject_template_name='registration/pw_reset_subject.txt',
            from_email=settings.AWS_SES_FROM_EMAIL
        ),
        name='password_reset'
    ),
    re_path(
        r'^password_reset/done/$',
        auth_views.PasswordResetDoneView.as_view(
            template_name='registration/pw_reset_done.html'
        ),
        name='password_reset_done'
    ),
    re_path(
        r'^reset/\
        (?P<uidb64>[0-9A-Za-z_\-]+)/\
        (?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,40})/$',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='registration/pw_reset_confirm.html'
        ),
        name='password_reset_confirm'
    ),
    re_path(
        r'^reset/done/$',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='registration/pw_reset_complete.html'
        ),
        name='password_reset_complete'
    )
]
