$(function () {
    $('[data-toggle="tooltip"]').tooltip({
        placement: 'top'
    });
    $("#jscontrols").append($("<label><input type='checkbox' id='mark'> Highlight unresponded questions</label>"));
    $("#mark").click(function (evt) {
        if ($("#mark").is(":checked")) {
            $(".answer.a0").css("background", "#FFFFDD");
        } else {
            $(".answer.a0").css("background", null);
        }
    });
});
