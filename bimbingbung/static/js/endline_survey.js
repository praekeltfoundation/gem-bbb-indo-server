$(document).ready(function() {
        var csrftoken;
        csrftoken = Cookies.get('csrftoken');

       $('.mark-receive-survey').each(function(index){
            $(this).change(function(){
                var self = $(this);
                self.prop("readonly", true);
                self.prop("disabled", true);
                $.ajax({
                    beforeSend: function(xhr, settings) {
                        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                            xhr.setRequestHeader("X-CSRFToken", csrftoken);
                        }
                    },
                    complete: function(data) {
                        self.prop("readonly", false);
                        self.prop("disabled", false);
                    },
                    url: '/admin/coach-surveys/survey/mark-can-receive/' + $(this).val() + '/',
                    method: "POST"
                });
            });
       });
});

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}