Updater = function() {
	this.url = 'ws://'+location.host+'/socket';
	this.oWebSocket;
};

Updater.prototype.start = function() {
	this.oWebSocket = new  WebSocket(this.url);
	var oThat = this;
	this.oWebSocket.onmessage = function(event) {
		aData = JSON.parse(event.data);
		oThat.updateProbe(aData);
	};
};

Updater.prototype.updateProbe = function(oProbe) {
	console.log(oProbe);
	var sId = oProbe.id;
	var oRow = $('#probe-'+sId);
	oRow.find('.code span').html(oProbe.lastCode);
};

oUpdater = new Updater();
oUpdater.start();
