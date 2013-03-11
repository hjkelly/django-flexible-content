// Use a closure to keep from cluttering the namespace.
(function ($) {
    /**
     * Update the area's item stats, both visible and invisible.
     */
    function updateMetadata() {
        // Update the item count
        itemCount = $('.fc-item').length;
        $('span.fc-item-counter').text(itemCount);

        // Update the prefixes.
        prefixes = [];
        // Collect each item's prefix
        $('.fc-item').each(function() {
            prefix = $(this).attr('data-form-prefix');
            prefixes.push(prefix);
        });
        $('input.fc-prefixes').val(prefixes.join(','));

        // Redo the ordering.
        $('.fc-item').each(function(zeroIndex) {
            $(this).find('input.fc-ordering').val(zeroIndex + 1);
        });
    }

    /**
     * Add an item of this type slug to the end of the content area.
     * @param {string} typeSlug     The type to get the template from.
     */
    function addItem(typeSlug) {
        template = fcFormTemplates[typeSlug]
        // If we encountered problems, notify the user instead of failing
        // silently.
        if (typeof(template) != 'string') {
            alert("Sorry, something went wrong. Tell a developer that "+
                  "the type you tried to add didn't have a form template "+
                  "(or perhaps we just aren't looking in the right "+
                  "place).");
        }

        // What number item is this?
        nextNumber = $('.fc-item').length + 1;

        // Take the next number and insert it in the template.
        pattern = new RegExp(fcFormPrefixPlaceholder, 'gm')
        // Replace that placeholder with our counter.
        html = template.replace(pattern, nextNumber);

        // Insert the HTML at the end of the content area.
        $('.fc-items').append(html);

        // Update the prefixes, item, etc.
        updateMetadata()
    }

    /**
     * For a given element, find its ancestor element that represents the item.
     * @param {jQuery} $descendent  The element to find the item for.
     */
    function getItem($descendent) {
        return $descendent.parents('.fc-item:first');
    }

    /**************************************************************************
        Register handlers for each item.
    **************************************************************************/

    $(document).ready(function() {
        // Update the prefixes, item, etc.
        updateMetadata()

        // Delete links should toggle the 
        $('.fc-items').on('click.delete', '.fc-delete', function(ev) {
            ev.preventDefault();
            $this = $(this);
            $item = getItem($this);

            // Add or remove the deleted class.
            $item.toggleClass('fc-deleted');
            // Update its input based on its visual class.
            $item.find('.fc-delete input[type=hidden]')
                 .val($item.hasClass('fc-deleted') ? 1 : 0);
        });

        $('.fc-items').on('click.moveDown', '.fc-move-down', function(ev) {
            ev.preventDefault();
            console.log("move down?");

            // What item are we dealing with?
            item = getItem($(this));
            // Get its position amongst the other fc-items.
            var index = item.index('.fc-item');
            var total = $('.fc-item').length;

            // If it's not at the botton, move it down.
            if (index < total-1) {
                nextItem = item.next('.fc-item');
                // Remove it and put it before the next item.
                item.remove()
                    .insertAfter(nextItem);
            }

            // Reorder the content items!
            updateMetadata();
        });

        $('.fc-items').on('click.moveUp', '.fc-move-up', function(ev) {
            ev.preventDefault();
            console.log("move up?");

            // What item are we dealing with?
            item = getItem($(this));
            // Get its position amongst the other fc-items.
            var index = item.index('.fc-item');

            // If it's not at the top, move it up.
            if (index != 0) {
                prevItem = item.prev('.fc-item');
                // Remove it and put it before the previous item.
                item.remove()
                    .insertBefore(prevItem);
            }

            // Reorder the content items!
            updateMetadata();
        });

        // Adding new items. These don't need on, since they can't change
        // after the page has loaded.
        $('.fc-add-item .fc-item-types a').click(function(ev) {
            ev.preventDefault();
            $this = $(this);

            // Append an item of this type to the form.
            addItem($this.attr('data-type-slug'));
        });
    });
})($);


/******************************************************************************
    function contentItemCounter(newCounter) {
        // TODO: Make this use the number of items in the DOM, not the
        // input's value.

        var hiddenCounterSelector = 'input.fc-item-counter';
        var displayCounterSelector = 'span.fc-item-counter';

        // If they're asking for the number.
        if (typeof(newCounter) == 'undefined') {
            return parseInt($(hiddenCounterSelector).eq(0).val());
        }
        else {
            // Make sure we're dealing with an integer.
            if (typeof(newCounter) == 'string') {
                newCounter = parseInt(newCounter);
            }
            // Update the hidden counter and the display.
            $(hiddenCounterSelector).val(newCounter);
            $(displayCounterSelector).html(newCounter);
        }
    }

    function updateOrdering() {
        // Update the ordering!
        ordering_fields = $('#fc-items input.ordering');
        num_items = ordering_fields.length;
        for (var i=0; i<num_items; i++) {
            $(ordering_fields[i]).val(i+1);
        }
    }

    function toggleContentItemDeleted(ev) {
        ev.preventDefault();

        // Is this item set to be deleted or not?
        link = $(this);
        label = $(this).find('span');
        input = $(this).find('input[type=hidden]');

        // If they're trying to delete it:
        if (input.val() == '0') {
            label.text("Wait! Don't delete this!");
            input.val(1);
            // Mark the content item as deleted.
            link.parentsUntil('.fc-item').parent().addClass('deleted');
        }
        // If they're trying to cancel deletion:
        else {
            label.text("Delete");
            input.val(0);
            // Undo the visual mark of the item being deleted.
            link.parentsUntil('.fc-item').parent().removeClass('deleted');
        }
    }

    function toggleContentItemAdvanced(ev) {
        ev.preventDefault();

        link = $(this);
        contentItem = link.parentsUntil('.fc-item').parent();
        advancedSection = contentItem.find('.advanced');

        // If the advanced stuff isn't shown right now:
        if (advancedSection.is(':visible')) {
            advancedSection.slideUp('fast');
            link.text("Show advanced...");
        }
        // If they're trying to cancel deletion:
        else {
            advancedSection.slideDown('fast');
            link.text("Hide advanced...");
        }
    }


    function registerContentItemHandlers() {
        // DELETE LINKS
        deleteLinks = $('.fc-item a.delete');
        // Remove the binding, so we don't get duplicates.
        deleteLinks.unbind('click', toggleContentItemDeleted);
        // Re-bind.
        deleteLinks.bind('click', toggleContentItemDeleted);

        // SHOW ADVANCED
        advancedLinks = $('.fc-item a.advanced-link');
        // Remove the binding, so we don't get duplicates.
        advancedLinks.unbind('click', toggleContentItemAdvanced);
        // Re-bind.
        advancedLinks.bind('click', toggleContentItemAdvanced);

        // DRAGGABLE/SORTABLE
        $('#fc-items').sortable({
            start: sortableStartHandler,
            stop: sortableStopHandler,
            revert: true
        });
        $('#fc-items .header').disableSelection();
        $('#fc-items .header *').disableSelection();
    }

    $(document).ready(function() {
        updateOrdering();
        registerContentItemHandlers();

        // Register event handlers on the 'add' buttons for each type.
        $('#fc-item-add-by-type a').click(function(ev) {
            ev.preventDefault();

            // Get the identifier for this content item type.
            slug = $(this).attr('data-type-slug');
            if (typeof(slug) != 'string') {
                alert("Sorry, something went wrong. Tell a developer that "+
                      "the type you tried add didn't have a slug (or perhaps "+
                      "we're looking in the wrong place).");
            }

            // Get the HTML that we'll use to make up the form.
            form_template = fcFormTemplates[slug];
            if (typeof(form_template) != 'string') {
                alert("Sorry, something went wrong. Tell a developer that "+
                      "the type you tried to add didn't have a form template "+
                      "(or perhaps we just aren't looking in the right "+
                      "place).");
            }
            console.log(form_template);

            // What will this new form's counter be?
            newItemCounter = contentItemCounter() + 1;

            // Generate the HTML for this item.
            placeholder = fcFormPrefixPlaceholder;
            // Escape non-regex-safe characters.
            placeholder = placeholder.replace(/(?=[\\^$*+?.()|{}[\]])/g, "\\");
            // Form a regular expression matching all instances on all lines.
            pattern = new RegExp(placeholder, 'gm')
            // Replace that placeholder with our counter.
            form_html = "<div class='fc-item'>" + 
                form_template.replace(pattern, newItemCounter) + "</div>";
            if (typeof(form_html) != 'string') {
                alert("Sorry, something went wrong. Tell a developer that we "+
                      "couldn't render the final form from the template.");
            }

            $('#fc-items').append(form_html);
            updateOrdering();
            registerContentItemHandlers();

            // Increment the counter.
            contentItemCounter(newItemCounter);
        });
    });
*/

