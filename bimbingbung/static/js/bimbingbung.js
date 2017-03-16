var currIndex = 0;
var list = document.getElementById("tip-nav-dots").getElementsByTagName("li");
var leftButton = document.getElementById("left-nav-button");
var rightButton = document.getElementById("right-nav-button");

window.onload = function() {
// var images = document.getElementsByTagName("img");
//    for(i = 0; i < images.length; ++i){
//        var image = images[i];
//        if(image.id != "left-nav-button" && image.id != "right-nav-button"){
//            image.style = "max-width:200px;max-height:200px;";
//        }
//    }

  checkButtonSource(0);
};

function empDot(int){
    if(int == -1){
        if(currIndex != 0){
            mySwipe.prev();
            list[currIndex].removeAttribute("id");
            currIndex = ((currIndex + list.length)-1) % list.length;
            list[currIndex].setAttribute("id", "activated");
            scroll(0,0);
        }
    }else{
        if(currIndex != (list.length - 1)){
            mySwipe.next();
            list[currIndex].removeAttribute("id");
            currIndex = (currIndex+1) % list.length;
            list[currIndex].setAttribute("id", "activated");
            scroll(0,0);
        }
    }
    checkButtonSource(currIndex);
}

function checkButtonSource(index){
    if(index == 0){
        leftButton.src="/static/img/Tips Buttons_Previous_OFF.svg";
    }
    if(index == 1){
        leftButton.src="/static/img/Tips Buttons_Previous_ON.svg";
    }
    if(index == (list.length-1)){
        rightButton.src="/static/img/Tips Buttons_Next_OFF.svg";
    }
    if(index == (list.length-2)){
        rightButton.src="/static/img/Tips Buttons_Next_ON.svg";
    }
}

var mySlideTransitionCallback = function(index, elem) {
    list[currIndex].removeAttribute("id");
    currIndex = index;
    list[currIndex].setAttribute("id", "activated");
    checkButtonSource(currIndex);
}


window.mySwipe = new Swipe(document.getElementById('slider'), {callback: mySlideTransitionCallback, continuous: false});
list[0].setAttribute("id", "activated");