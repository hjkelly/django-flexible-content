from django import forms

from .models import MyItem

class MyItemForm(ContentItemForm):
    class Meta:
        model = MyItem

