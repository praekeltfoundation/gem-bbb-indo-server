var currIndex = 0;
var list = document.getElementById("tip-nav").getElementsByTagName("li");

function empDot(int){
    if(int === -1){
        list[currIndex].removeAttribute("id");
        currIndex = ((currIndex + list.length)-1) % list.length;
        list[currIndex].setAttribute("id", "activated");
    }else{
        list[currIndex].removeAttribute("id");
        currIndex = (currIndex+1) % list.length;
        list[currIndex].setAttribute("id", "activated");
    }
}