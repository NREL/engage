from django.db import models
from django.utils.html import mark_safe


class Help_Guide(models.Model):
    class Meta:
        db_table = "help_guide"
        verbose_name_plural = "[Admin] Help Guide"

    key = models.CharField(max_length=200)
    html = models.TextField(blank=True, null=True)

    def __str__(self):
        return '%s' % (self.key)

    def safe_html(self):
        """ Allows stored html to be rendered in HTML """
        return mark_safe(self.html)

    @classmethod
    def get_safe_html(cls, key):
        """ Retrieve the html content based on key """
        record = cls.objects.filter(key=key).first()
        if record:
            return mark_safe(record.html)
        else:
            return 'Not Available'
