Updater = function() {
	this.url = 'ws://'+location.host+'/socket';
	this.oWebSocket;
};

Updater.prototype.start = function() {
	this.oWebSocket = new  WebSocket(this.url);
	var oThat = this;
	this.oWebSocket.onmessage = function(event) {
		var sRcvdData = event.data
		var aFrame = sRcvdData.split('|||');
		if (2 != aFrame.length) {
			throw 'Invalid frame received from socket';
		}
		var oData = {
			type: aFrame[0],
			message:JSON.parse(aFrame[1])
		};
		switch(oData.type) {
			case 'probeUpdate':
				oThat.updateProbe(oData.message);
				break;
			case 'nbClientUpdate':
				oThat.updateClientNumber(oData.message.nbClient);
				break;
		}
	};
};

Updater.prototype.updateProbe = function(oProbe) {
	var sId = oProbe.id;
	var oRow = $('#probe-'+sId);
	oRow.find('.code span').html(oProbe.lastCode);
};

Updater.prototype.updateClientNumber = function(iNumber) {
	var oClientNode = $('#nbClient');
	oClientNode.html(iNumber);	
}

oUpdater = new Updater();
oUpdater.start();
