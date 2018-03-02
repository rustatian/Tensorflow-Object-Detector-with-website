var canvasFace = document.getElementById('canvas-face');
var context = canvasFace.getContext('2d');
var img = new Image();
var socketOpened = false;

// show loading notice
context.fillStyle = '#333';
context.fillText('Loading...', canvasFace.width / 2 - 30, canvasFace.height / 3);

function newSocket() {
  return new WebSocket("wss://<URL>:443");
}

var socket = newSocket();

socket.onopen = function() {
  socketOpened = true;
}
socket.onmessage = function(event) {
	// var uint8Arr = new Uint8Array(event.data);
	// var str = String.fromCharCode.apply(null, uint8Arr);
	// var base64String = btoa(str);

	img.onload = function () {
		context.drawImage(this, 0, 0, canvasFace.width, canvasFace.height);
	};
	img.src = 'data:image/jpeg;base64,' + event.data;
};

socket.onclose = function() {
  socketOpened = false;
  socket = newSocket();
}
