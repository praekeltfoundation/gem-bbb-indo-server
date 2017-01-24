$(document).ready(function() {
       $('.mark-is-read').each(function(index){
            $(this).change(function(){
                /*console.log($(this).val() + ':' + this.checked);*/
                $(".mark-is-read").prop("readonly", true);
                $.ajax({
                    url: '/admin/participants/mark-read/' + $(this).val() + '/',
                    method: "POST"
                });
                $(".mark-is-read").prop("readonly", false);
            });
       });
});