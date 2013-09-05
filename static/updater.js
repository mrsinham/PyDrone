Updater = function() {
	this.url = 'ws://'+location.host+'/socket';
	this.oWebSocket;
};

Updater.prototype.start = function() {
	this.oWebSocket = new  WebSocket(this.url);
	this.oWebSocket.onmessage = function(event) {
		console.log(event.data);
	};
};

oUpdater = new Updater();
oUpdater.start();
