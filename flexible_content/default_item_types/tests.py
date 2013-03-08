from django.test import TestCase

from mock_project.test_app.models import MyArea

from .models import Video


class VideoTest(TestCase):
    def setUp(self):
        # Create an area with regular ordering (first item first).
        self.area = MyArea.objects.create(title="Blah")

    def test_youtube_validate_good_id(self):
        """
        Make sure a valid youtube ID can be validated.
        """

        # Create fake form data.
        fake_POST = {'ordering': 1, 'service': 'youtube', 'video_id': "RnAAIHBCubM"}
        # Insert the two fields to tie this object to the area.
        fake_POST.update(self.area.get_generic_fk_form_data())

        # Get the form using that fake POST data.
        form = Video().get_form(fake_POST)
        # Try to save it.
        form.save()

        if not form.instance.pk:
            self.fail("Couldn't validate an existing Vimeo ID.")

    def test_youtube_validate_invalid_id(self):
        """
        Make sure a valid youtube ID is rejected when invalid.
        """

        # Create fake form data.
        fake_POST = {'ordering': 1, 'service': 'youtube', 'video_id': "abc123"}
        # Insert the two fields to tie this object to the area.
        fake_POST.update(self.area.get_generic_fk_form_data())

        # Get the form using that fake POST data.
        form = Video().get_form(fake_POST)
        # Try to save it.
        try:
            form.save()
        except ValueError:
            pass
        else:
            self.fail("Form allowed an invalid Vimeo ID.")

    def test_vimeo_validate_good_id(self):
        """
        Make sure a valid vimeo ID can be validated.
        """

        # Create fake form data.
        fake_POST = {'ordering': 1, 'service': 'vimeo', 'video_id': "59338758"}
        # Insert the two fields to tie this object to the area.
        fake_POST.update(self.area.get_generic_fk_form_data())

        # Get the form using that fake POST data.
        form = Video().get_form(fake_POST)
        # Try to save it.
        form.save()

        if not form.instance.pk:
            self.fail("Couldn't validate an existing Vimeo ID.")

    def test_vimeo_validate_invalid_id(self):
        """
        Make sure a valid vimeo ID is rejected when invalid.
        """

        # Create fake form data.
        fake_POST = {'ordering': 1, 'service': 'vimeo', 'video_id': "a1b2c3d4"}
        # Insert the two fields to tie this object to the area.
        fake_POST.update(self.area.get_generic_fk_form_data())

        # Get the form using that fake POST data.
        form = Video().get_form(fake_POST)
        # Try to save it.
        try:
            form.save()
        except ValueError:
            pass
        else:
            self.fail("Form allowed an invalid Vimeo ID.")

