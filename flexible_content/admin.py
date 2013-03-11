"""
I am sorry for this file.

You see, Django does have support for inlines. But not inlines of different 
types. So these hacks take over the space between `fieldsets` and `inlines`
and manage these content items on their own.

The first time I wrote this, I replaced the add_view and change_view methods
altogether. This is bad because it meant any changes to the stock Django 
methods don't propagate to the overridden methods.

This version is a complete rewrite with the goal of using super() instead of
nuking ModelAdmin's add_view and change_view. That means that all the value
they add has to happen before and after the super() call. Consequently, parts
of this are less than obvious, because it's not given a piece of data 
explicitly.

Ideally, this would be redone in the future to be more elegant - perhaps 
replacing the views altogether, or allowing front-end editing via an API.
"""

from django import forms
from django.contrib import admin
from django.contrib.admin.util import unquote
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_protect

from .models import BaseItem, TemporaryArea


csrf_protect_m = method_decorator(csrf_protect)

FORM_PREFIX_TEMPLATE = 'fc-item-{counter}'
FORM_PREFIX_PLACEHOLDER = 'PLACEHOLDER'
def get_form_prefix(counter=FORM_PREFIX_PLACEHOLDER):
    return FORM_PREFIX_TEMPLATE.format(counter=counter)


class ContentAreaAdminForm(forms.ModelForm):
    """
    Make the area's validation depend on its items' validation.
    """

    # This will be our hook into the area's validation process from add_view
    # and change_view. If we don't mark this field as True, it'll fail with
    # a validation error. Let it be unchecked here, but raise a general (non-
    # field-specific) error in the clean method.
    all_items_validated = forms.BooleanField(required=False,
                                             widget=forms.HiddenInput)

    def clean(self):
        d = self.cleaned_data

        # Get the value they submitted for item validation, cast it to an int
        # (so an accidental '0' string won't pass as true), and evaluate it
        # boolean-ly.
        all_items_validated = bool(int(d.get('all_items_validated', '0')))
        if not all_items_validated:
            message = _("One of the content items didn't validate. Please "
                        "check them and try again.")
            raise forms.ValidationError(message)

        return d

class ContentAreaAdmin(admin.ModelAdmin):
    """
    Allow management of content items from within the admin.

    Since ModelAdmin itself is complex, use 'fc_' as a prefix to all
    attributes that we add here. Hopefully this will make it more clear when
    we're working in here vs. in ModelAdmin or elsewhere.
    """
    change_form_template = 'flexible-content/change-form.html'
    save_on_top = True

    @csrf_protect_m
    @transaction.commit_on_success
    def add_view(self, request, form_url='', extra_context=None):
        """
        Override the add/create view to allow editing and validation of items.
        """

        # Add in the necessary context.
        if extra_context is None:
            extra_context = {}
        extra_context = self.fc_get_context(request)

        # Save the items they submitted.
        temp_area = None
        if request.method == 'POST':
            temp_area = self.fc_save_items(request,
                                           forms=extra_context['fc_forms'])

        # Call ModelAdmin's add_view.
        response = (super(ContentAreaAdmin, self).
                    add_view(request, form_url, extra_context))

        # If the above object was saved, attach our items and save them.
        new_area = getattr(request, 'new_content_area_object', None)
        if temp_area is not None and new_area is not None:
            temp_area.migrate_items_to(new_area)

        return response

    @csrf_protect_m
    @transaction.commit_on_success
    def change_view(self, request, object_id, form_url='', extra_context=None):
        """
        Override the change view to allow editing and validation of items.
        """
        # Redundant super().change_view will do this again, but meh.
        obj = self.get_object(request, unquote(object_id))

        # Add in the necessary context.
        if extra_context is None:
            extra_context = {}
        extra_context = self.fc_get_context(request, obj)

        if request.method == 'POST':
            self.fc_save_items(request, area=obj,
                               forms=extra_context['fc_forms'])

        # Call ModelAdmin's add_view.
        response = (super(ContentAreaAdmin, self).
                    change_view(request, object_id, form_url, extra_context))

        return response

    def fc_save_items(self, request, area=None, forms=None):
        """
        For each form, create/update objects.
        """
        all_items_validated = True

        # Ensure we don't accidentally do this on a GET request.
        if request.method != 'POST':
            raise Exception("You shouldn't ever call save_items with a GET "
                            "request!")

        # If the current area doesn't exist yet, create a temporary one to save
        # the items to.
        if area is None:
            using_temp_area = True
            area = TemporaryArea.objects.create()
        else:
            using_temp_area = False

        # If there are any forms, loop through them.
        if len(forms):
            # We'll need the data on the area we're saving it to.
            area_ct = area.get_content_type().pk
            area_id = area.pk

            for f in forms:

                # If this form's data includes a non-zero value for the delete
                # field, they want it deleted.
                if f.should_be_deleted():
                    # We only need to actively delete it if it's already in
                    # the database.
                    if f.already_exists():
                        f.instance.delete()
                    # Don't do anything else, if they didn't want their changes
                    # saved.
                    continue

                # Ensure that the object we're saving is assigned to the proper
                # area, especially if the real content area doesn't exist yet.
                f.data.update({
                    '{}-content_area_ct'.format(f.prefix): area_ct,
                    '{}-content_area_id'.format(f.prefix): area_id,
                })

                # Save the form.
                try:
                    f.save()
                # Suppress these errors, since the Django admin doesn't catch
                # them like it does for the forms it knows about. We'll address
                # this later.
                except ValueError as e:
                    all_items_validated = False

        # Set the main area's form validation field based on our assessment
        # of the items' validation. If this value is zero, it will trigger
        # the admin to fail validation because we told it items were invalid.
        request.POST = request.POST.copy()
        request.POST.update({
            'all_items_validated': all_items_validated and '1' or '0',
        })

        # Only return something if we're using a temporary area.
        if using_temp_area:
            return area
        # Otherwise, return nothing.
        else:
            return None

    def fc_get_context(self, request, obj=None):
        """
        Add flexible_content context we'll need for add_view and change_view.
        """
        return {
            'fc_types': [t() for t in BaseItem.get_configured_types()],
            'fc_forms': self.fc_get_forms(request, obj=obj),
            'fc_form_prefix_placeholder': FORM_PREFIX_PLACEHOLDER,
        }

    def fc_get_form_model_by_prefix(self, request, prefix):
        # Try to load the model class via the ContentType they suggested.
        ct_pk = request.POST.get('{}-ct'.format(prefix), None)
        try:
            model_class = ContentType.objects.get(pk=ct_pk).model_class()
        # Be ready for a content type not to exist. Don't worry about the
        # AttributeError - the doesnotexist should be raised first.
        except ContentType.DoesNotExist:
            message = ("Form said its type was that of ContentType {}, but "
                       "that ContentType couldn't be found in the "
                       "database.".format(ct_pk))
            raise ValueError(message)

        # If the model isn't a subclass of BaseItem, that's also a problem.
        if not issubclass(model_class, BaseItem):
            message = ("For ContentType {}, we got the model {}, which isn't "
                       "even a subclass of BaseItem.".
                       format(ct_pk, model_class))
            raise Exception(message)

        return model_class
        
    def fc_get_forms_from_POST(self, request):
        forms = []

        # What prefixes are there?
        prefixes = [p for p in 
                    request.POST.get('fc-prefixes', '').split(',') if p]

        # Loop through each submitted item and process its data.
        for p in prefixes:

            # Check the PK for this prefix
            pk = request.POST.get('{}-pk'.format(p), None)
            # If this prefix is for an existing item, load its data.
            instance = None
            if pk:
                try:
                    instance = (BaseItem.objects.filter(pk=pk).
                                select_subclasses()[:1][0])
                except IndexError:
                    message = ("Form reported update of BaseItem with id {}, "
                               "but no such BaseItem exists.".format(pk))
                    raise ValueError(message)

            # We need to copy the POST data so it can be updated (QueryDicts
            # are immutable). Plus, there's less redundant data.

            # Append a hypen to the prefix. Django does this in the form, but
            # we need to prevent getting fc-item-10 when we ask for fc-item-1,
            # and adding the hyphen will avoid that.
            search_prefix = '{}-'.format(p)
            # Assemble a dictionary of only this form's data.
            this_form_data = dict([(k, v) for (k, v) in request.POST.items()
                                   if k.startswith(p)])

            # Alright, it's time to create the form! If we found an instance,
            # use that to create it.
            if isinstance(instance, BaseItem):
                form = instance.get_form(data=this_form_data,
                                         files=request.FILES, prefix=p)
            # Otherwise, we'll have to get the model from the content type
            # field first.
            else:
                model_class = self.fc_get_form_model_by_prefix(request, p)

                form = model_class().get_form(data=this_form_data,
                                              files=request.FILES, prefix=p)

            # Append the form to the end of the list.
            forms.append(form)

        return forms

    def fc_get_forms(self, request, obj=None):
        """
        Use the request to get the forms that should be rendered to the page.
        """
        forms = []

        # Are they POSTing data, or should we merely get it from the DB?
        if request.method == 'POST':
            forms = self.fc_get_forms_from_POST(request)
        # If this is a GET on an existing area.
        elif obj:
            for i in obj.items:
                prefix = get_form_prefix(len(forms)+1)
                forms.append(i.get_form(prefix=prefix))
        # If this is a GET on an area's ADD page.
        else:
            forms = []

        return forms

    def get_fieldsets(self, request, obj=None):
        """
        Ensure that 'all_items_validated' never shows up in the fieldsets.
        """
        fieldsets = super(ContentAreaAdmin, self).get_fieldsets(request, obj)

        # Loop through the fieldset declaration and remove the tricksy field.
        for fs in fieldsets:
            fs_info = fs[1]
            if 'all_items_validated' in fs_info['fields']:
                fs_info['fields'] = [field for field in fs_info['fields']
                                     if field != 'all_items_validated']
        return fieldsets

    def save_model(self, request, obj, form, change):
        """
        If this is a new item and not a change, save the new obj somewhere we
        can find it!

        This is necessary because we don't have a hook for this within 
        add_view on either side of the super() call.
        """

        # Perpetuate the call to ModelAdmin.
        super(ContentAreaAdmin, self).save_model(request, obj, form, change)

        # If this was a freshly saved ContentArea, save it on the request.
        if not change:
            request.new_content_area_object = obj

