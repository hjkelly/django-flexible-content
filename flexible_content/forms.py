from django import forms
from django.template.loader import render_to_string


class BaseItemForm(forms.ModelForm):
    content_item_template = 'flexible-content/_single-item-form.html'

    delete = forms.BooleanField(initial=False, required=False)

    class Meta(object):
        pass

    def already_exists(self):
        """
        Report on whether or not this instance has been saved.
        """
        return bool(getattr(self.instance, 'pk', None))

    def as_content_item(self):
        """
        Instead of as_p, as_ul, and the like, render a content item as
        it shows in the admin.
        """
        return render_to_string(self.content_item_template, {'form': self})

    def get_unique_fields(self):
        """
        Which fields aren't part of BaseItem? These will be presented front
        and center.
        """
        baseitem_fields = (
            'content_area_ct',
            'content_area_id',
            'ordering',
            'delete',
        )

        # Loop through each field:
        unique_fields = []
        for f in self.visible_fields():
            # So long as it's not one of the baseitem fields, add it to our
            # list.
            if f.name not in baseitem_fields:
                unique_fields.append(f)
        return unique_fields

    def should_be_deleted(self):
        """
        Look at the incoming data and figure out whether it's marked for
        deletion.
        """
        return bool(int(self.data.get('{}-delete'.format(self.prefix), '0')))

