$(document).ready(function() {
        var csrftoken;
        csrftoken = Cookies.get('csrftoken');

       $('.mark-receive-survey').each(function(index){
            $(this).change(function(){
                $(".mark-receive-survey").prop("readonly", true);
                $.ajax({
                    beforeSend: function(xhr, settings) {
                        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                            xhr.setRequestHeader("X-CSRFToken", csrftoken);
                        }
                    },
                    url: '/admin/content/survey/mark-can-receive/' + $(this).val() + '/',
                    method: "POST"
                });
                $(".mark-receive-survey").prop("readonly", false);
            });
       });
});

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}