django-flexible-content
=======================

You can't always predict the shape your content will take. `django-flexible-content` lets you manage rich content without sacrificing flexibility or CMS usability.

What does it do?
----------------

With `django-flexible-content`:
-   Your models can hold one or more content items (text, image, video embed)
-   You can skin each type of item in the Django template language
-   You can create new item types to suit your needs

Why would I use it?
-------------------

Scenarios where `django-flexible-content` might help you:
-   A blog where CMS users need precise control over each post's content (for example, placing a tweet in the middle of the page that complies with Twitter's display requirements).
    -   With a Tweet item type, the user could enter a tweet's ID or URL in and display it per a standard Django template. This tweet could also appear between two giant chunks of text (other items, too).
-   A site with a bunch of randomly-placed pages, even ones with a contact form, slideshow, or an introductory video.
    -   Your pages can be managed in the CMS, and each one of those types of custom content can be a content item type.
-   You want stylistic consistency that WYSIWYG-uploaded images can't provide.
    -   A user uploads an image, and *you* generate its markup, not some JavaScript code.

Default Setup
-------------

Requirements:
-   Your project is configured to load templates from app directories ([it is by default](https://docs.djangoproject.com/en/1.5/ref/settings/#template-loaders)).
-   Your project uses the staticfiles app. It must also be configured to find staticfiles in app directories ([it is by default](https://docs.djangoproject.com/en/1.5/ref/contrib/staticfiles/#staticfiles-finders)).

That said, let's get started:

1.  Install the package.
    ```
    pip install django-flexible-content
    ```
2.  Add it to your settings file.

    ```python
    INSTALLED_APPS = (
        # ...
        'flexible_content',
        'flexible_content.default_item_types',  # Optional: Five basic types of content item.
    )
    ```

    Also, the thinote that the app_directories template loaders must be enabled[TEMPLATE_LOADERS] should be enabled, but this is Django's default behavior.
3.  Sync your database.

    `python manage.py syncdb`
4.  For each model you want to add content items to, subclass ContentArea.

    ```python
    # my_project/my_app/models.py:
    from django.db import models
    from flexible_content.models import ContentArea

    class BlogPost(ContentArea):
        title = models.CharField(max_length=50)
        slug = models.CharField(max_length=50)

        class Meta:
            verbose_name = "blog post"
    ```

    Note that this won't change your database schema at all: ContentArea is an abstract class that just adds helper functionality.
5.  For each model that subclasses ContentArea, define a custom ModelAdmin that subclasses ContentAreaAdmin.

    ```python
    # my_project/my_app/admin.py:
    from django.contrib import admin
    from flexible_content.admin import ContentAreaAdmin
    from .models import BlogPost

    class BlogPostAdmin(ContentAreaAdmin):
        pass

    admin.sites.register(BlogPost, BlogPostAdmin)
    ```

Custom Templates
----------------

You can define your own templates that replace the ones included with the `default_item_types` app.

1.  In one of your own app's `templates` directory (or in a folder specified by the `TEMPLATE_DIRS` setting), create a folder called `flexible-content`.
2.  Inside of that directory, create an HTML file based on the type's slug:
    ```
    flexible-content/download.html
    flexible-content/image.html
    flexible-content/plain-text.html
    flexible-content/raw-html.html
    flexible-content/video.html
    ```
3.  Ensure that those templates will be discovered first:
    -   If you placed them in an app's `templates` directory, make sure that app comes before `flexible_content.default_item_types` in your `INSTALLED_APPS` setting.
    -   If you placed them in an arbitrary template directory, make sure:
        -   That directory is specified in the `TEMPLATES_DIRS` setting.
        -   The filesystem loader (which uses `TEMPLATE_DIRS`) comes before the app_directories loader in the `TEMPLATE_LOADERS` setting.

Custom Item Types
-----------------

I'll write this documentation soon, I promise! Until then, see `flexible_content_types.default_item_types.models` for examples. Once you've created those models that subclass BaseItem, you also need to specify that model in your settings:
```
FLEXIBLE_CONTENT = {
    'ITEM_TYPES': (
        'my_app.RichText',
        'default_item_types.Image'
    ),
}
```
