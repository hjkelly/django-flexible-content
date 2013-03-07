from django import forms

from .models import PlainText, RawHTML, Image, Download, Video


class PlainTextForm(forms.ModelForm):
    class Meta:
        model = PlainText


class RawHTMLForm(forms.ModelForm):
    class Meta:
        model = RawHTML


class ImageForm(forms.ModelForm):
    class Meta:
        model = Image


class DownloadForm(forms.ModelForm):
    class Meta:
        model = Download


class VideoForm(forms.ModelForm):
    class Meta:
        model = Video

