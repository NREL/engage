
$( document ).ready(function() {

    var alert_msg = $("#login_form").data('alert');
    if (alert_msg != '') {
        alert(alert_msg)
    };

    $('#register_btn, #register_cancel').on('click', function() {
        $('#login-label').toggle();
        $('#register_btn').toggleClass('hide');
        $('#register_cancel').toggleClass('hide');
        $('#login_form').toggle('hide');
        $('#registration_form').toggle('hide');
    })

});

function registration() {

    var form = $("#registration_form"),
        url = form.data('action'),
        formdata = form.serialize();

    $.ajax({
        type: "POST",
        url: url,
        data: formdata,
        success: function(data)
        {
            alert(data['message']);
        }
    });

};