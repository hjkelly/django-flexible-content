from django.db import models

from flexible_content.forms import ContentItemForm
from flexible_content.models import ContentArea, ContentItem


class MyArea(ContentArea):
    title = models.CharField(max_length=50)


class MyItem(BaseItem):
    my_number = models.IntegerField()

    class FlexibleContentInfo:
        description = _("Hopefully this works!")
        type_slug = 'my-item'

    class Meta(BaseItem.Meta):
        verbose_name = _("My Item")

