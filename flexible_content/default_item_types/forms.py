from django import forms
from django.utils.translation import ugettext as _
from django.utils import simplejson

import requests
from flexible_content.forms import BaseItemForm

from .models import Video


class VideoForm(BaseItemForm):
    class Meta(BaseItemForm.Meta):
        model = Video

    def clean_video_id(self):
        """
        Ensure that, for the given service, the video_id is valid.
        """
        failed = False
        d = self.cleaned_data
        service = d.get('service')
        # Get the video id and clear whitespace on either side.
        video_id = d.get('video_id', '').strip()

        # Validate using YouTube's API:
        if service == 'youtube':
            url = ('http://gdata.youtube.com/feeds/api/videos/{}?alt=json'.
                   format(video_id))
            data = requests.get(url)
            # Ensure we can parse the JSON data.
            try:
                json = simplejson.loads(data.text)
            # If not, mark this as a failure.
            except ValueError:
                failed = True

        # Validate using Vimeo's API:
        elif service == 'vimeo':
            data = requests.get('http://vimeo.com/api/v2/video/{}.json'.
                                format(video_id))
            # Ensure we can parse the JSON data.
            try:
                json = simplejson.loads(data.text)
            # If not, mark this as a failure.
            except ValueError:
                failed = True

        # Respond based on the outcome.
        if failed:
            message = _("Couldn't validate video id using {} API. Please "
                        "verify it exists and check for "
                        "typos.".format(service))
            raise forms.ValidationError(message)

        return video_id

