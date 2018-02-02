$(document).ready(function() {

    $('[data-toggle="popover"]').popover({
        container: 'body',
        html: true,
        placement: 'right',
        trigger: 'hover',
        title: function() {
            return $(this).parent().find('.popover-title').html();
        },
        content: function() {
            return $(this).parent().find('.popover-content').html();
        }
    });

});
