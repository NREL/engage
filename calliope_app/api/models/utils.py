from django.db import models

from datetime import datetime
import pytz


# ----- Override Base Django Classes: QuerySet, Manager

class EngageQuerySet(models.query.QuerySet):
    """
    QuerySet whose delete() does not delete items, but instead marks the
    rows as not active by setting the deleted timestamp field
    """

    def delete(self):
        self._cascade_mark_delete(self)

    def hard_delete(self):
        for model in self:
            model.delete()

    @classmethod
    def _cascade_mark_delete(cls, query_in):
        objects = list(query_in.all())
        query_in.update(deleted=datetime.now(tz=pytz.UTC))
        for obj in objects:
            for field in obj._meta.get_fields():
                if field.one_to_many:
                    attr = field.name
                    try:
                        query_out = getattr(obj, '{}'.format(attr))
                    except AttributeError:
                        query_out = getattr(obj, '{}_set'.format(attr))
                    cls._cascade_mark_delete(query_out)


class EngageManager(models.Manager):
    """
    Manager that returns a DeactivateQuerySet,
    to prevent object deletion.
    """

    def get_queryset(self):
        objects = EngageQuerySet(self.model, using=self._db)
        return objects.filter(deleted=None)
