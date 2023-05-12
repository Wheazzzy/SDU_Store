
//----------HERE GONNA BE LIKE WHEN YOU NAVIGATE TO BUTTON IT'S GONNA BE BIGGER,
//AND WHEN YOU OUT THIS BUTTON IT GONNA BE A SMALL---------------------------------------
function big(element){
    element.style.fontSize = "50px";
}

function small(element){
    element.style.fontSize = "30px";
}
// -------------------------END HERE BIG SMALL------------------------------

//---------------THIS FUNCTION WORKING LIKE THIS WHEN YOU NAVIGATE TO CITY AND CLICK IT CHANGED-------------------------
function change(element){
    let a = element.innerHTML;
    switch(a){
        case "-Almaty-":
            document.getElementById("map").src="./static/almaty.png";
            document.getElementById("slogan").innerHTML="Almaty, Mametova 47 & Rozybakieva 247a";
            document.getElementById("number").innerHTML="+7-747-189-56-16 || +7-778-948-98-00";
            break;
        case "-Astana-":
            document.getElementById("map").src="./static/astana.png";
            document.getElementById("slogan").innerHTML="Astana, Uly Dala 7/7 & Qabanbai Batyr 62";
            document.getElementById("number").innerHTML="+7-777-062-13-09 || +7-747-189-56-16";
            break;
        case "-Shymkent-":
            document.getElementById("map").src="./static/shym.png";
            document.getElementById("slogan").innerHTML="Shymkent, Tauke khan 43a";
            document.getElementById("number").innerHTML="+7-747-189-56-16 || +7-778-948-98-00";
            break;
        case "-Aqtau-":
            document.getElementById("map").src="./static/aqtau.png";
            document.getElementById("slogan").innerHTML="Aqtau, 17 mkr. 95";
            document.getElementById("number").innerHTML="+7-778-546-07-83 || +7-747-189-56-16";
            break;
        case "-Aqtobe-":
            document.getElementById("map").src="./static/aqtobe.png";
            document.getElementById("slogan").innerHTML=" Aqtobe, Mametova 4";
            document.getElementById("number").innerHTML="+7-777-70-78 || +7-747-189-56-16";
            break;
    }
}
// -----------------------------END CHANGE FUNCTION------------------------------------------->
