from django.db import models
from django.utils.translation import ugettext as _

from flexible_content.models import ContentArea, BaseItem


class MyArea(ContentArea):
    title = models.CharField(max_length=50)


class MyItem(BaseItem):
    my_number = models.IntegerField()

    class FlexibleContentInfo:
        description = _("Hopefully this works!")
        type_slug = 'my-item'

    class Meta:
        verbose_name = _("My Item")
