var currIndex = 0;
var list = document.getElementById("tip-nav-dots").getElementsByTagName("li");
var leftButton = document.getElementById("left-nav-button");
var rightButton = document.getElementById("right-nav-button");

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
    if(currIndex == 0){
        leftButton.src="/static/img/Tips Buttons_Previous_OFF.svg";
    }
    if(currIndex == 1){
        leftButton.src="/static/img/Tips Buttons_Previous_ON.svg";
    }
    if(currIndex == (list.length-1)){
        rightButton.src="/static/img/Tips Buttons_Next_OFF.svg";
    }
    if(currIndex == (list.length-2)){
        rightButton.src="/static/img/Tips Buttons_Next_ON.svg";
    }
}