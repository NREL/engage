from django.contrib import admin

from account.models import User_Profile



class User_Profile_Admin(admin.ModelAdmin):
    list_display = ['id', 'user', 'organization',
                    'timezone', 'activation_uuid']


admin.site.register(User_Profile, User_Profile_Admin)
