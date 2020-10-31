from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from gitd.core.constants import Services


class Deployment(models.Model):
    service = models.CharField(_("service"), max_length=30, choices=Services.CHOICES)
    delivery = models.CharField(_("delivery identifier"), max_length=1024, blank=True)
    date = models.DateTimeField(_("date"), default=timezone.now)

    class Meta:
        verbose_name = _("deployment")
        verbose_name_plural = _("deployments")
        db_table = "deployments"
        ordering = ("-date",)

    def __str__(self):
        return f"{self.delivery} ({self.service})"

    def __repr__(self):
        return f"Deployment(service={self.service}, delivery={self.delivery})"
