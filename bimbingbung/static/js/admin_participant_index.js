$(document).ready(function() {
        var csrftoken;
        csrftoken = Cookies.get('csrftoken');

       $('.mark-is-read').each(function(index){
            $(this).change(function(){
                /*console.log($(this).val() + ':' + this.checked);*/
                $(".mark-is-read").prop("readonly", true);
                $.ajax({
                    beforeSend: function(xhr, settings) {
                        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                            xhr.setRequestHeader("X-CSRFToken", csrftoken);
                        }
                    },
                    url: '/admin/participants/mark-read/' + $(this).val() + '/',
                    method: "POST"
                });
                $(".mark-is-read").prop("readonly", false);
            });
       });
});

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}