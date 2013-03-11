from django import forms
from django.contrib import admin

from flexible_content.admin import ContentAreaAdmin, ContentAreaAdminForm

from .models import MyArea


class MyAreaAdminForm(ContentAreaAdminForm):
    class Meta:
        model = MyArea


class MyAreaAdmin(ContentAreaAdmin):
    form = MyAreaAdminForm


admin.site.register(MyArea, MyAreaAdmin)
