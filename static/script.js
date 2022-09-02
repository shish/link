$(function () {
    $('[data-toggle="tooltip"]').tooltip({
        placement: 'top'
    });
    $("#jscontrols").append($("<label><input type='checkbox' id='mark'> Highlight unresponded questions</label>"));
    $("#mark").click(function (evt) {
        if ($("#mark").is(":checked")) {
            $("table.zebra").addClass("highlight-unmarked");
        } else {
            $("table.zebra").removeClass("highlight-unmarked");
        }
    });
});
