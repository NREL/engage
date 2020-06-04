from django.contrib import admin
from .models import CeleryTask


# Register your models here.
class CeleryTaskAdmin(admin.ModelAdmin):

	def _date_start(self, obj):
		if not obj.date_start:
			return ""
		return obj.date_start.strftime("%Y-%m-%d %H:%M:%S")

	def _date_done(self, obj):
		if not obj.date_done:
			return ""
		return obj.date_done.strftime("%Y-%m-%d %H:%M:%S")

	list_display = ['id', 'task_id', 'status', '_date_start', '_date_done', 'result', 'traceback']


admin.site.register(CeleryTask, CeleryTaskAdmin)
