var minus = document.querySelector('.minus'),
    plus = document.querySelector('.plus'),
    value = document.querySelector('.value'),
    users = document.querySelector('.users'),
    websocket = new WebSocket("ws://127.0.0.1:6789/");
minus.onclick = function (event) {
    websocket.send(JSON.stringify({action: 'minus'}));
}
plus.onclick = function (event) {
    websocket.send(JSON.stringify({action: 'plus'}));
}
websocket.onmessage = function (event) {
    data = JSON.parse(event.data);
    switch (data.type) {
        case 'state':
            value.textContent = data.value;
            break;
        case 'users':
            users.textContent = (
                data.count.toString() + " user" +
                (data.count == 1 ? "" : "s"));
            break;
        default:
            console.error(
                "unsupported event", data);
    }
};