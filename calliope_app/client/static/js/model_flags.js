$( document ).ready(function(){
    $('.flag-delete').on('click', function(){
        $.ajax({
            url: '/' + LANGUAGE_CODE + '/api/remove_flags/',
            type: 'POST',
            data: {
                'model_uuid': $('#header').data('model_uuid'),
                'form_data': JSON.stringify([{'type':$(this).attr('name').split('||')[0], 'id':$(this).attr('name').split('||')[1]}]),
                'csrfmiddlewaretoken': getCookie('csrftoken'),
            },
            dataType: 'json',
            success: function (data) {
                if (data['message'] != "Success."){
                    alert(data['message']);
                }
                else{
                    window.onbeforeunload = null;
                    location.reload();
                }
            }
        });
    });
});