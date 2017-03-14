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
                    url: '/admin/content/participants/mark-read/' + $(this).val() + '/',
                    method: "POST"
                });
                $(".mark-is-read").prop("readonly", false);
            });
       });

       $('.mark-is-shortlisted').each(function(index){
            $(this).change(function(){
                /*console.log($(this).val() + ':' + this.checked);*/
                $(".mark-is-shortlisted").prop("readonly", true);
                $.ajax({
                    beforeSend: function(xhr, settings) {
                        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                            xhr.setRequestHeader("X-CSRFToken", csrftoken);
                        }
                    },
                    url: '/admin/content/participants/mark-shortlisted/' + $(this).val() + '/',
                    method: "POST"
                });
                $(".mark-is-shortlisted").prop("readonly", false);
            });
       });

       $('.mark-is-winner').each(function(index){
            $(this).change(function(){
                /*console.log($(this).val() + ':' + this.checked);*/
                $(".mark-is-winner").prop("readonly", true);
                $.ajax({
                    beforeSend: function(xhr, settings) {
                        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                            xhr.setRequestHeader("X-CSRFToken", csrftoken);
                        }
                    },
                    url: '/admin/content/participants/mark-winner/' + $(this).val() + '/',
                    method: "POST"
                });
                $(".mark-is-winner").prop("readonly", false);
            });
       });
});

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}