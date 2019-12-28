var speed = 0.3;

var body = document.querySelector("body");
body.onload = function() {
    var field = document.querySelector("#playfield");
    var websocket = new WebSocket("ws://192.168.1.146:6789/");
    var status = document.querySelector("#status");
    var words = document.querySelector("#words");
    var score = document.querySelector("#score")
    var players = {};
    var validations = [];
    var my_id = null;

    var width = field.clientWidth;
    var height = field.clientHeight;
    var AR = 2;
    var offx = 0;
    var offy = 0;

    function resize(ev) {
        if(window.innerWidth / 2 > window.innerHeight - 120) {
            document.querySelector("#doublecontainer").style.width = Math.floor((window.innerHeight - 150) * 2) + "px";
        } else {
            document.querySelector("#doublecontainer").style.width = "auto";
        }
        width = field.clientWidth;
        height = field.clientHeight;                
    }
    resize();

    window.onresize = resize
    
    field.onclick = function(ev) {
        console.log(ev);
        var x = ev.offsetX / field.clientWidth * AR;
        var y = ev.offsetY / field.clientHeight;
        console.log(x,y);
        websocket.send(JSON.stringify({action:"target", x:x, y:y}))
    }

    function updatePlayer(p) {
        var pid = p['pid']
        var pObj = players[pid];
        var el = null;
        if(!pObj) {
            el = document.createElement("div");
            field.appendChild(el);
            pObj = {'elem': el, 'tx':p['tx'], 'ty':p['ty'], 'x':p['x'], 'y':p['y']}
            players[pid] = pObj;
        } else {
            pObj.tx = p.tx;
            pObj.ty = p.ty;
            var dx = pObj.x - p.x;
            var dy = pObj.y - p.y;
            if(dx*dx+dy*dy > 0.1 * 0.1) {
                pObj.x = p.x;
                pObj.y = p.y;
            }
        }
        el = pObj['elem'];
        el.innerText = p['symbol'].toUpperCase();
        el.style.left = p['x'] * width + "px";
        el.style.top = p['y'] * height + "px";
        if(pid == my_id) {
            el.className = "player me";
        } else {
            el.className = "player";
        }        
    }

    function updateValidations(boxes) {
        validations.forEach(elem => {
            elem.style.opacity = "0";
        });
        boxes.forEach((box, i) => {
            var elem = validations[i]
            if(!elem) {
                elem = document.createElement("div")
                validations.push(elem);
                field.appendChild(elem);
            }
            elem.style.opacity = "1";
            if(box.valid) {
                elem.className = "validation valid";
            } else {
                elem.className = "validation";
            }
            elem.style.left = Math.floor(box.x1 / AR * width) - 45 + "px"
            elem.style.top = Math.floor(box.y1 * height) - 45 + "px"
            elem.style.width = Math.floor((box.x2 - box.x1) / AR * width) + 90 + "px"
            elem.style.height = Math.floor((box.y2 - box.y1) * height) + 90 + "px"
        });
    }

    function updateState(state) {
        var status_str = "";
        if(state.state == "playing") {
            status_str = Math.floor(state.round_time);
        } else if (state.state == "victory") {
            status_str = "Good work!!";
        } else if (state.state == "defeat") {
            status_str = "You lose! :(";
        }
        status.innerText = status_str;
        state.players.forEach(updatePlayer);
        var pids = {}
        state.players.forEach(p => {
            pids[p.pid] = p;
        });
        Object.keys(players).forEach(pid => {
            if(pids[pid] === undefined) {
                field.removeChild(players[pid].elem);
                delete players[pid];
            }
        });
        updateValidations(state.validation_boxes);
        words.innerText = state.victory_words;
        score.innerText = "Score: " + state.score;
    }
    
    websocket.onmessage = function (event) {
        
        data = JSON.parse(event.data);
        switch (data.type) {
            case 'state':
                updateState(data.value)
                break;
            case 'joined':
                my_id = data.value['your_id'];
                break;
            default:
                console.error(
                    "unsupported event", data);
        }
    };
    
    function update(timestamp) {
        var dt = (timestamp - lastRender) / 1000;
        Object.keys(players).forEach(function(k) {
            var pObj = players[k];
            var dx = pObj.tx - pObj.x;
            var dy = pObj.ty - pObj.y;
            if(dx != 0 && dy != 0) {
                var dist = Math.sqrt(dx*dx+dy*dy);
                if(dist < dt * speed) {
                    pObj.x = pObj.tx;
                    pObj.y = pObj.ty;
                } else {
                    pObj.x += dx / dist * dt * speed;
                    pObj.y += dy / dist * dt * speed;
                }
            }
            
            pObj.elem.style.left = Math.floor(pObj.x / AR * width) + "px";
            pObj.elem.style.top = Math.floor(pObj.y * height) + "px";        
        })
        lastRender = timestamp
        window.requestAnimationFrame(update);
    }
    
    var lastRender = 0;
    window.requestAnimationFrame(update);    
}