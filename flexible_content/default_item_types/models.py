from django.db import models
from django.utils.translation import ugettext as _

from flexible_content.models import BaseItem
from flexible_content.utils import get_app_settings


class PlainText(BaseItem):
    text = models.TextField()

    class FlexibleContentInfo:
        description = _("This text won't be interpreted, other than to add "
                        "paragraph/line breaks. In other words, you can't put "
                        "HTML here.")
        name = "Plain Text"
        type_slug = 'plain-text'

    class Meta:
        verbose_name = _("Plain Text")


class RawHTML(BaseItem):
    html = models.TextField()

    class FlexibleContentInfo:
        description = _("Insert custom scripts or snippets of HTML here. Be "
                        "careful, though: you *can* break the site this way.")

    class Meta:
        verbose_name = _("Raw HTML")


class Image(BaseItem):
    uploaded_file = models.FileField(upload_to='flexible-content/images')

    class FlexibleContentInfo:
        description = _("Upload an image and have it displayed as the site "
                        "chooses. You can also specify a heading or caption. "
                        "Note that it's usually best to put an image *before* "
                        "any text it should appear alongside.")

    class Meta:
        verbose_name = _("Image")


class Download(BaseItem):
    uploaded_file = models.FileField(upload_to='flexible-content/downloads')

    class FlexibleContentInfo:
        description = _("Upload a file and have it advertised as the site "
                        "chooses. You can also specify a heading or caption. "
                        "Note that it's usually best to put a download "
                        "*before* any text it should appear alongside.")

    class Meta:
        verbose_name = _("Download")


def get_default_video_service():
    settings = get_app_settings()
    return settings.get('DEFAULT_VIDEO_SERVICE', '')

class Video(BaseItem):
    SERVICE_CHOICES = (
        ('youtube', _('YouTube')),
        ('vimeo', _('Vimeo')),
    )
    # HELP TEXT (for fields)
    HELP_VIDEO_ID = _("The number/code/identifier for your video. You can "
                      "usually find it in the URL, but each video service is "
                      "different.")

    service = models.CharField(max_length=25,
                               default=lambda: get_default_video_service())
    video_id = models.CharField(verbose_name=_("Video ID"), max_length=100,
                                help_text=HELP_VIDEO_ID)

    class FlexibleContentInfo:
        description = _("Give details about a video and have it displayed as "
                        "the site chooses. You can also specify a heading or "
                        "caption. Note that it's usually best to put an video "
                        "*before* any text it should appear alongside.")

    class Meta:
        verbose_name = _("Video")

    def get_form_class(self):
        from .forms import VideoForm
        return VideoForm


# Register all of the types below
DEFAULT_TYPES = (PlainText, RawHTML, Image, Download, Video)
