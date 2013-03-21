django-flexible-content
=======================

Sometimes it's easy to edit content on your site. Update some page's template, and push it live. You're in control, or at least things don't need to change often.

For the rest of the time, there's `django-flexible-content`.

What does it do?
----------------

`django-flexible-content` lets you:
-   Turn your Django model (i.e. `BlogEntry`) into a `ContentArea`, which can then hold content items (i.e. plain text, HTML, a video embed, an image, etc)
-   Define your own content item types. By subclassing `BaseItem`, you can create new models with whatever fields you want, and add these to any content area.
-   Have full control over the template for each type of item. So if you have an image with a heading and a caption, you can form a proper `figure` with `fighead` and `figcaption`. Style it to your heart's content.

Why would I use it?
-------------------

Say you develop a site for someone who wants to put content on their own blog. Sure, you could give them a WYSIWYG editor and trust them to upload/drop in their own images. But what if that's not enough?
1.  What if we want to enhance the styling on those images?
2.  What if you want to add extra stuff like a `<fighead>` or `<figcaption>`? There's no way they can do that in a user-friendly way, anywhere they want.
3.  What if you just want to ensure all images (or videos, or whatever) are shown consistently across the site?

