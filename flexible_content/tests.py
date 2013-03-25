from django.core.exceptions import ImproperlyConfigured
from django.contrib.admin.sites import AdminSite
from django.contrib.contenttypes.models import ContentType
from django.test import SimpleTestCase, TestCase
from django.test.client import Client, RequestFactory
from django.test.utils import override_settings

from mock_project.test_app.models import MyArea, MyItem

from .admin import ContentAreaAdmin, FORM_PREFIX_PLACEHOLDER, get_form_prefix
from .models import BaseItem, ContentArea, TemporaryArea
from .default_item_types.models import (DEFAULT_TYPES, PlainText, RawHTML,
                                        Image, Download, Video)
from .utils import get_app_settings, get_models_from_strings


CUSTOM_TYPES_STRING = (
    'default_item_types.PlainText',
    'default_item_types.Video',
    'test_app.MyItem',
)
CUSTOM_TYPES_CLASSES = (
    PlainText,
    Video,
    MyItem,
)


class TestDataMixin(object):
    # Load in a basic area with two types.
    fixtures = ['test-data.json']
    data_for_another_area = {
        'title': "New Page with Two Item",
        'fc-prefixes': 'fc-item-1,fc-item-2',
        # ITEM 1: Leave all non-required fields blank to make sure they're
        # robustly overwritten.
        'fc-item-1-content_area_ct': '',
        'fc-item-1-content_area_id': '',
        'fc-item-1-ct': ContentType.objects.get_for_model(PlainText).pk,
        'fc-item-1-pk': '',
        'fc-item-1-delete': 0,
        'fc-item-1-ordering': 2,
        'fc-item-1-text': "Blah blah blah.\n\nYippee.",
        # ITEM 2: Leave all non-required fields out to make sure they're
        # added in.
        'fc-item-2-ordering': 1,
        'fc-item-2-delete': 0,
        'fc-item-2-ct': ContentType.objects.get_for_model(RawHTML).pk,
        'fc-item-2-html': "<p>Testing!&amp;</p>",
    }
    data_for_updating_first_area = {
        'title': "Our original area, but updated",
        'fc-prefixes': 'fc-item-1,fc-item-2,fc-item-3,fc-item-4',

        # ITEM 1: Update the text and swap its place with item 2. Leave the
        # content area and stuff blank, to make sure it overwrites them.
        'fc-item-1-content_area_ct': '',
        'fc-item-1-content_area_id': '',
        'fc-item-1-pk': 1,  # Must stay consistent with our JSON fixture
        'fc-item-1-ct': ContentType.objects.get_for_model(PlainText).pk,
        'fc-item-1-ordering': 2,
        'fc-item-1-delete': 0,
        'fc-item-1-text': "Blah blah blah.\n\nYippee.",

        # ITEM 2: Delete it! And leave all non-required fields out to make
        # sure they're added in.
        'fc-item-2-ordering': 1,
        'fc-item-2-delete': 1,
        'fc-item-2-ct': ContentType.objects.get_for_model(Video).pk,
        'fc-item-2-pk': 2,  # Must stay consistent with our JSON fixture
        'fc-item-2-service': "vimeo",
        'fc-item-2-video_id': "59338758",

        # ITEM 3: An additional item! But delete it right away.
        'fc-item-3-ordering': 3,
        'fc-item-3-delete': 1,
        'fc-item-3-ct': ContentType.objects.get_for_model(RawHTML).pk,
        'fc-item-3-html': "<p>lkajsdlkfj alksjdfaklsf</p>",

        # ITEM 4: Add another item, but this time keep it!
        'fc-item-4-ordering': 4,
        'fc-item-4-delete': 0,
        'fc-item-4-ct': ContentType.objects.get_for_model(PlainText).pk,
        'fc-item-4-text': "blah blah blah blah new item",

    }

    @property
    def area(self):
        return MyArea.objects.get(pk=1)

    @property
    def item_1(self):
        return PlainText.objects.get(pk=1)

    @property
    def item_2(self):
        return Video.objects.get(pk=2)


class ConfiguredTypesTest(SimpleTestCase):
    """
    Make sure the app reports the proper types as being available, for any
    given configuration.
    """

    # Use blank settings to make sure it recovers by using the default types.
    @override_settings(FLEXIBLE_CONTENT=None)
    def test_without_settings(self):
        from .default_item_types.models import DEFAULT_TYPES
        # Make sure it gave us the default types.
        types = BaseItem.get_configured_types()
        self.assertEqual(types, DEFAULT_TYPES)

    # Use invalid settings to make sure it complains about it.
    @override_settings(FLEXIBLE_CONTENT="Hi!")
    def test_with_bad_settings(self):
        try:
            types = BaseItem.get_configured_types()
        except ImproperlyConfigured:
            pass
        else:
            self.fail("BaseItem.get_configured_types() didn't raise an "
                      "exception when the settings were way wrong (a string "
                      "instead of a dict).")

    # Give it a nonexistent app and model to make sure it complains.
    @override_settings(FLEXIBLE_CONTENT={'ITEM_TYPES': ('fake.DoesNotExist',)})
    def test_with_nonexistent_type(self):
        try:
            types = BaseItem.get_configured_types()
        except ImportError:
            pass
        else:
            self.fail("BaseItem.get_configured_types() didn't raise an "
                      "exception when given a non-existent model.")

    # Configure the project's settings to use the custom type strings above.
    @override_settings(FLEXIBLE_CONTENT={'ITEM_TYPES': CUSTOM_TYPES_STRING})
    def test_with_custom_types(self):
        types = BaseItem.get_configured_types()
        # Make sure it matches our tuple of those classes.
        self.assertEqual(types, CUSTOM_TYPES_CLASSES)


@override_settings(FLEXIBLE_CONTENT={'ITEM_TYPES': CUSTOM_TYPES_STRING})
class AreaTest(TestCase):
    """
    Ensure that all of the basic functions work, at least somewhat.
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


@override_settings(FLEXIBLE_CONTENT={'ITEM_TYPES': CUSTOM_TYPES_STRING})
class ItemTest(TestDataMixin, TestCase):
    """
    Make sure we can create, edit, and delete items of different types.
    """

    def setUp(self):
        pass

    def test_get_form_prefix_default(self):
        self.assertEqual(get_form_prefix(), 'fc-item-PLACEHOLDER')

    def test_get_form_prefix_counter(self):
        self.assertEqual(get_form_prefix(counter=1), 'fc-item-1')

    def test_get_form_template(self):
        """
        Make sure we can get the HTML for an item.
        """
        html = self.item_1.get_form_template().as_content_item()

        if FORM_PREFIX_PLACEHOLDER not in html:
            self.fail("The form template doesn't include the placeholder "
                      "text.")

    def test_get_casted(self):
        """
        Make sure we can cast a basic BaseItem instance.
        """
        item = BaseItem.objects.all()[0]
        self.assertEqual(type(item), BaseItem)

        casted_item = item.get_casted()
        self.assertNotEqual(type(casted_item), BaseItem)

    def test_get_type_description(self):
        """
        Make sure that we can get a type's description.
        """
        self.assertEqual(self.item_1.get_type_description(),
                         self.item_1.__class__.FlexibleContentInfo.description)

    def test_create_simple_type(self):
        """
        Can we create an instance of an item without a defined form?
        """
        # Create a blank item.
        new_item = MyItem()

        # Create some fake data to submit.
        fake_POST = {
            'content_area_id': self.area.pk,
            'content_area_ct': self.area.get_content_type().pk,
            'ordering': 3,
            'my_number': 6090,
        }

        # Set up the form with this data and save it!
        form_with_data = new_item.get_form(data=fake_POST)
        form_with_data.save()

        # See if the form has an instance with valid primary key.
        if not getattr(form_with_data.instance, 'pk'):
            self.fail("Couldn't create a MyItem by saving faked data through "
                      "a form.")

    def test_create_type_with_custom_form(self):
        """
        Can we create an instance of an item that uses a custom form?
        """
        new_item = Video()

        # Create a form instance without a saved instance.
        initial_form = new_item.get_form()

        # Ensure the form has the video-ish fields on it.
        if 'video_id' not in initial_form.fields:
            self.fail("Couldn't get a form instance from an unsaved item.")

        # Re-render the form and supply data.
        fake_POST = {
            'content_area_id': self.area.pk,
            'content_area_ct': self.area.get_content_type().pk,
            'ordering': 3,
            'service': 'vimeo',
            'video_id': "59338758",
        }

        form_with_data = new_item.get_form(data=fake_POST)
        # Save it!
        form_with_data.save()

        # See if the form has an instance with valid primary key.
        if not getattr(form_with_data.instance, 'pk'):
            self.fail("Couldn't create a video by saving faked data through "
                      "a form.")

    def test_get_instance_form(self):
        """
        Can we get the form for an existing content item?
        """
        # Ensure that we can get the form and that its instance matches
        # the one we used to get the form. Weird!
        self.assertEqual(self.item_1.get_form().instance,
                         self.item_1)

    def test_get_type_name(self):
        """
        Can we use a specified type name, or generate one automatically?
        """

        # For a class that specifies a type name, do we get what we expect?
        self.assertEqual(PlainText().get_type_name(), 'Plain Text')

        # What about a type that doesn't specify a name?
        self.assertEqual(Video().get_type_name(), 'Video')

    def test_get_type_slug(self):
        """
        Can we use a specified type slug, or generate one automatically?
        """

        # For a class that specifies a type slug, do we get what we expect?
        self.assertEqual(self.item_1.get_type_slug(), 'plain-text')

        # What about a type that doesn't specify a slug?
        self.assertEqual(self.item_2.get_type_slug(), 'video')

    def test_get_template_name(self):
        """
        Make sure that we can get a type's template name/path.
        """
        self.assertEqual(self.item_2.get_template_name(),
                         'flexible-content/video.html')

    def test_delete_base_item(self):
        """
        Ensure that the subclass is deleted too, for generic FK integrity.
        """
        self.fail("You haven't finished this test yet.")

    def test_delete_item_subclass(self):
        """
        Ensure that the base item is deleted too, for generic FK integrity.
        """
        self.fail("You haven't finished this test yet.")


class AdminUnitTest(TestDataMixin, TestCase):
    # Test the custom admin methods to make sure they handle input properly.

    def setUp(self):
        self.factory = RequestFactory()
        self.site = AdminSite()
        self.admin = ContentAreaAdmin(MyArea, self.site)

    def test_fc_get_context(self):
        # Make sure that, when we're just loading a page, it gives us the
        # proper context.
        request = self.factory.get('/admin/test_app/myarea/{}/'.
                                   format(self.area.pk))

        # Call the method!
        context = self.admin.fc_get_context(request, obj=self.area)

        # FC_TYPES
        # Test the number of types being sent to the template.
        self.assertEqual(len(context['fc_types']),
                         len(BaseItem.get_configured_types()))
        # Ensure we're getting an instance of the model.
        self.assertEqual(context['fc_types'][0].__class__,
                         BaseItem.get_configured_types()[0])

        # FC_FORMS
        # Are we getting the right number of forms for this area?
        self.assertEqual(len(context['fc_forms']), 2)
        # Make sure the first form's instance is the first item on this area.
        self.assertEqual(context['fc_forms'][0].instance,
                         self.area.items[0])

        # the prefix
        self.assertEqual(context['fc_form_prefix_placeholder'],
                         FORM_PREFIX_PLACEHOLDER)

    def test_fc_get_form_model_by_prefix(self):
        # For a given item in the POST vars, we should be able to load the
        # corresponding model.

        # Generate a fake request object that we can pass to the method.
        plain_text_ct = ContentType.objects.get_for_model(PlainText)
        request = self.factory.post('/admin/test_app/myarea/add/',
                                    {'fc-item-1-ct': plain_text_ct.pk})
        # Get the model for that item.
        model = self.admin.fc_get_form_model_by_prefix(request, 'fc-item-1')

        # Ensure the admin it gave us was the one we wanted.
        self.assertEqual(model, PlainText)

    def test_fc_get_forms_from_POST(self):
        # Make sure fc_get_forms_from_POST can load unbound forms.

        # Start by creating a new a new area ----------------------------------
        data = self.data_for_another_area
        request = self.factory.post('/admin/test_app/myarea/add/', data)

        # Get the forms based on that request.
        forms = self.admin.fc_get_forms_from_POST(request)

        # Make sure everything's hunkey-dorey!

        # Ensure neither form has an instance.
        self.assertEqual(forms[0].instance.pk, None)
        self.assertEqual(forms[1].instance.pk, None)

        # Ensure that the forms have been passed the right POST data.
        self.assertEqual(forms[0].data['fc-item-1-text'],
                         data['fc-item-1-text'])
        self.assertEqual(forms[1].data['fc-item-2-html'],
                         data['fc-item-2-html'])

        # Now make sure we can update an existing item ------------------------
        url = '/admin/test_app/myarea/{}'.format(self.area.pk)
        data = self.data_for_updating_first_area
        request = self.factory.post(url, data)

        # Get the forms based on that request.
        forms = self.admin.fc_get_forms_from_POST(request)

        # Ensure the length.
        self.assertEqual(len(forms), 4)

        # We should find that the second two items are about to be deleted,
        # but not the first.
        self.assertEqual(forms[0].data['fc-item-1-delete'], '0')
        self.assertEqual(forms[1].data['fc-item-2-delete'], '1')
        self.assertEqual(forms[2].data['fc-item-3-delete'], '1')
        self.assertEqual(forms[3].data['fc-item-4-delete'], '0')

        # Make sure a basic, type-specific piece of info came through with
        # each.
        self.assertEqual(forms[0].data['fc-item-1-text'],
                         data['fc-item-1-text'])
        self.assertEqual(forms[1].data['fc-item-2-video_id'],
                         data['fc-item-2-video_id'])
        self.assertEqual(forms[2].data['fc-item-3-html'],
                         data['fc-item-3-html'])
        self.assertEqual(forms[3].data['fc-item-4-text'],
                         data['fc-item-4-text'])

    def test_fc_get_forms_GET_add(self):
        self.fail("You haven't finished this test yet.")

    def test_fc_get_forms_GET_change(self):
        """
        Forms for existing items should always be bound and have a PK.
        """
        request = self.factory.get('/admin/test_app/myarea/{}/'.
                                   format(self.area.pk))

        forms = self.admin.fc_get_forms(request, obj=self.area)

        # Ensure that each of the existing items is still bound to the proper
        # form.
        existing_item_pks = [i.pk for i in self.area.items]
        for f in forms:
            pk = getattr(f.instance, 'pk', None)
            # If it has a PK, remove that PK from our checklist
            if pk is not None:
                existing_item_pks.remove(pk)

        # Are there any existing items that weren't found in the forms?
        self.assertEqual(len(existing_item_pks), 0)

    def test_fc_get_forms_POST_change(self):
        """
        Forms for existing items should always be bound and have a PK.
        """
        url = '/admin/test_app/myarea/{}/'.format(self.area.pk)
        data = self.data_for_updating_first_area
        request = self.factory.post(url, data)

        forms = self.admin.fc_get_forms(request, obj=self.area)

        # Ensure that each of the existing items is still bound to the proper
        # form.
        existing_item_pks = [i.pk for i in self.area.items]
        for f in forms:
            pk = getattr(f.instance, 'pk', None)
            # If it has a PK, remove that PK from our checklist
            if pk is not None:
                existing_item_pks.remove(pk)

        # Are there any existing items that weren't found in the forms?
        self.assertEqual(len(existing_item_pks), 0)

    def test_save_model(self):
        self.fail("You haven't finished this test yet.")


class AdminIntegrationTest(TestDataMixin, TestCase):
    # Ensure that requests can be made as expected.

    def setUp(self):
        self.client = Client()
        self.client.login(username='test', password='test')

    def test_create_itemless_area(self):
        # Ensure that we can create an area without content items (edge case).

        # What page will we hit?
        url = '/admin/test_app/myarea/add/'
        data = {
            'title': "Test Page - no items",
            'fc-prefixes': '',
        }

        # Get the areas that already exist.
        existing_area_pks = tuple(MyArea.objects.values_list('pk', flat=True))

        # Hit the admin with our 'create new area' request.
        response = self.client.post(url, data)

        # Get newly-created areas. There should only be one, and it should
        # have the title we're looking for.
        new_areas = tuple(MyArea.objects.exclude(pk__in=existing_area_pks))

        # Make sure all is well.
        self.assertEqual(len(new_areas), 1)
        self.assertEqual(new_areas[0].title, data['title'])

    def test_create_area_with_items(self):
        # Ensure that we can create an area a few items.

        # What page will we hit?
        url = '/admin/test_app/myarea/add/'
        data = self.data_for_another_area

        # Get the areas that already exist.
        existing_area_pks = tuple(MyArea.objects.values_list('pk', flat=True))
        existing_item_pks = tuple(BaseItem.objects.
                                  values_list('pk', flat=True))

        # Hit the admin with our 'create new area' request.
        response = self.client.post(url, data, follow=True)

        # Get newly-created areas. Make sure there's only one and that its data
        # is correct.
        new_areas = tuple(MyArea.objects.exclude(pk__in=existing_area_pks))
        self.assertEqual(len(new_areas), 1)
        self.assertEqual(new_areas[0].title, data['title'])

        # Get the new items. Are there two, and is their data accurate?
        new_items = tuple(new_areas[0].items.exclude(pk__in=existing_item_pks))
        self.assertEqual(len(new_items), 2)
        # We should get the HTML first, since we put them in in the reverse
        # order of their ordering number.
        self.assertEqual(new_items[0].html, data['fc-item-2-html'])
        self.assertEqual(new_items[1].text, data['fc-item-1-text'])

    def test_update_area_delete_item(self):
        # Ensure that we can update an existing area and delete one item.

        this_area_pk = self.area.pk
        url = '/admin/test_app/myarea/{}/'.format(this_area_pk)
        data = self.data_for_updating_first_area

        # Get the areas that already exist.
        self.assertEqual(len(self.area.items), 2)

        # Hit the admin with our 'update this area' request.
        response = self.client.post(url, data)

        # Make sure our area is still there.
        try:
            area = MyArea.objects.get(pk=this_area_pk)
        except MyArea.DoesNotExist:
            self.fail("For some reason, the area was deleted when trying to "
                      "delete one of its items.")
        self.assertEqual(area.title, data['title'])

        # Make sure we still have two items. The second should have been
        # deleted, another one never completed (marked as deleted before saved)
        # and another that was genuinely added. So combined with the one that
        # was merely updated, that makes two.
        self.assertEqual(len(self.area.items), 2)

        # Make sure the first one has the updated text, and still has the same
        # primary key.
        first_item = area.items[0]
        self.assertEqual(first_item.text, data['fc-item-1-text'])
        self.assertEqual(first_item.pk, data['fc-item-1-pk'])

        # Make sure the new item (with ordering four; the second remaining)
        # was saved and has the right ContentType and everything.
        second_item = area.items[1]
        self.assertEqual(second_item.text, data['fc-item-4-text'])
        self.assertEqual(second_item.get_content_type().pk,
                         data['fc-item-4-ct'])
        self.assertEqual(second_item.ordering, data['fc-item-4-ordering'])

