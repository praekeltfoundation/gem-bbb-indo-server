var currIndex = 0;
var list = document.getElementById("tip-nav-dots").getElementsByTagName("li");

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
}