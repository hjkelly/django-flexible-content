from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, TestCase
from django.test.utils import override_settings

from mock_project.test_app.models import MyArea, MyItem

from .models import ContentArea, BaseItem
from .default_item_types.models import (DEFAULT_TYPES, PlainText, RawHTML,
                                        Image, Download, Video)
from .utils import get_app_settings, get_models_from_strings


CUSTOM_TYPES_STRING = (
    'flexible_content.default_item_types.models.PlainText',
    'flexible_content.default_item_types.models.Video',
    'mock_project.test_app.models.MyItem',
)
CUSTOM_TYPES_CLASSES = (
    PlainText,
    Video,
    MyItem,
)


class ConfiguredTypesTest(SimpleTestCase):
    """
    Make sure the app reports the proper types as being available, for any
    given configuration.
    """

    @override_settings(IPANEMA=None)
    def test_without_settings(self):
        from .default_item_types.models import DEFAULT_TYPES
        # Make sure it gave us the default types.
        types = BaseItem.get_configured_types()
        self.assertEqual(types, DEFAULT_TYPES)

    @override_settings(IPANEMA="Hi!")
    def test_with_bad_settings(self):
        # Make sure we get an exception.
        try:
            types = BaseItem.get_configured_types()
        except ImproperlyConfigured as e:
            pass
        else:
            self.fail("Bad settings didn't raise an exception.")

    @override_settings(IPANEMA={'ITEM_TYPES': CUSTOM_TYPES_STRING})
    def test_with_custom_types(self):
        types = BaseItem.get_configured_types()
        # Make sure we get an exception.
        self.assertEqual(types, CUSTOM_TYPES_CLASSES)


@override_settings(IPANEMA={'ITEM_TYPES': CUSTOM_TYPES_STRING})
class AreaTest(TestCase):
    """
    Ensure that all of the basic functions we need can be 
    """
    
    def setUp(self):
        # Create an area with regular ordering (first item first).
        self.area_a = MyArea.objects.create(title="Blah")
        self.item_a1 = MyItem.objects.create(ordering=1,
                                             content_area=self.area_a,
                                             my_number=81)
        self.item_a2 = PlainText.objects.create(ordering=2,
                                                content_area=self.area_a,
                                                text="blarg! blalkdjf HI!")

        # Create another area with flipped items - create the second one first,
        # to make sure their ordering number takes precedence over their PK.
        self.area_b = MyArea.objects.create(title="Foo")
        self.item_b2 = RawHTML.objects.create(ordering=2,
                                              content_area=self.area_b,
                                              html="<p>Blah blah blah.</p>")
        self.item_b1 = Video.objects.create(ordering=1,
                                            content_area=self.area_b,
                                            service='vimeo',
                                            video_id="59338758")

    def test_get_items_via_area(self):
        """
        Areas should get a list of their items, and in the right order.
        """
        # Use the content_items property (actually a method) to get area A's
        # items. Listify them, so we can do an assertEqual.
        items = list(self.area_a.items)

        self.assertEqual(items, [self.item_a1, self.item_a2])

    def test_get_items_via_manager(self):
        """
        Areas should get a list of their items, and in the right order.
        """
        # Use the BaseItem manager to fetch the area's items. Listify them,
        # so we can do an assertEqual.
        items = list(BaseItem.objects.get_for_area(self.area_b))

        self.assertEqual(items, [self.item_b1, self.item_b2])

    def test_get_rendered_content(self):
        """
        Areas should be able to get their HTML on demand, and the result
        should contain the data from the models.
        """
        content_a = self.area_a.get_rendered_content()

        # Make sure the content from both items appears somewhere in the
        # output!
        if str(self.item_a1.my_number) not in content_a:
            self.fail("Couldn't find first item's my_number ({}) in rendered "
                      "content.".format(self.item_a1.my_number))
        if self.item_a2.text not in content_a:
            self.fail("Couldn't find second item's text ({}) in rendered "
                      "content.".format(self.item_a2.text))


@override_settings(IPANEMA={'ITEM_TYPES': CUSTOM_TYPES_STRING})
class ItemTest(TestCase):
    """
    Make sure we can create, edit, and delete items of different types.
    """

    def setUp(self):
        # Create an area with regular ordering (first item first).
        self.area = MyArea.objects.create(title="Blah")
        self.item_1 = MyItem.objects.create(ordering=1,
                                            content_area=self.area,
                                            my_number=81)
        self.item_2 = Video.objects.create(ordering=2,
                                           content_area=self.area,
                                           service='vimeo',
                                           video_id="59338758")

    def test_get_description(self):
        """
        Make sure that we can get a type's template name/path.
        """
        self.assertEqual(self.item_2.get_template_name(),
                         'flexible-content/video.html')

    def test_create_from_nothing(self):
        """
        Can we get a blank form for an item that only has a type?
        """
        new_item = Video()

        # Create a form instance without a saved instance.
        initial_form = new_item.get_form()

        # Ensure the form has the video-ish fields on it.
        if 'video_id' not in initial_form.fields:
            self.fail(_("Couldn't get a form instance from an unsaved item."))

        # Re-render the form and supply data.
        form_with_data = new_item.get_form({'ordering': 3,
                                            'content_area': self.area,
                                            'service': 'vimeo',
                                            'video_id': '60903598'})
        # Save it!
        form_with_data.save()
        
        # See if the form has an instance with valid primary key.
        if not getattr(form_with_data.instance, 'pk'):
            self.fail(_("Couldn't create a video by saving faked data through "
                        "a form."))

    def test_get_instance_form(self):
        """
        Can we get the form for an existing content item?
        """
        # Ensure that we can get the form and that its instance matches
        # the one we used to get the form. Weird!
        self.assertEqual(self.item_1.get_form().instance,
                         self.item_1)

    def test_get_type_slug(self):
        """
        Can we use a specified type slug, or generate one automatically?
        """

        # For a class that specifies a type slug, do we get what we expect?
        self.assertEqual(self.item_1.get_type_slug(), 'my-item')

        # What about a type that doesn't specify a slug?
        self.assertEqual(self.item_2.get_type_slug(), 'video')

    def test_get_template_name(self):
        """
        Make sure that we can get a type's template name/path.
        """
        self.assertEqual(self.item_2.get_template_name(),
                         'flexible-content/video.html')

