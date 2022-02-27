$(function () {
    $('[data-toggle="tooltip"]').tooltip({
        placement: 'top'
    });
    $("#jscontrols").append($("<label><input type='checkbox' id='mark'> Highlight unresponded questions</label>"));
    $("#mark").click(function (evt) {
        if ($("#mark").is(":checked")) {
            $("table.zebra")[0].classList.add("highlight-unmarked")
        } else {
            $("table.zebra")[0].classList.remove("highlight-unmarked")
        }
    });
});
