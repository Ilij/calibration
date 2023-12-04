var touchStart = null;
var touchPosition = null;

function TouchStart(e){
    console.log( e.changedTouches.length);
    touchStart = {x: e.changedTouches[0].clientX,
                  y: e.changedTouches[0].clientY };
    touchPosition = { x: touchStart.x,
                      y: touchStart.y};
}

function TouchMove(e){
    console.log( e.changedTouches.length);
    touchPosition = {x: e.changedTouches[0].clientX,
                     y: e.changedTouches[0].clientY };
}

function TouchEnd(e){
    console.log( e.changedTouches.length);
    console.log('TouchEnd');
}

function TouchCancel(e){
    console.log( e.changedTouches.length);
    console.log('TouchCancel');
}