from django.db import models
from django.utils.translation import gettext_lazy as _

class TimeStampAbstractModel(models.Model):
    created_at = models.DateTimeField(_('дата добавления'), auto_now_add=True)
    updated_at = models.DateTimeField(_('дата изменения'), auto_now=True)

    class Meta:
        abstract = True
