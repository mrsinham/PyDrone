ViewHelper = function() {

};


ViewHelper.prototype.getBadgeClassByCode = function(iCode) {
	if (200 === iCode) {
		return 'badge-success';
	} else if (400 <= iCode) {
		return 'badge-warning';
	} else if (500 <= iCode) {
		return 'badge-important';
	} else {
		return 'badge-inverse';
	}
};

ViewHelper.prototype.getRowClassByCode = function(iCode) {
	if (iCode != 200) {
		return 'warning';
	}
	return '';
};
Updater = function() {
	this.url = 'ws://'+location.host+'/socket';
	this.oWebSocket;
	this.oHelper = new ViewHelper();
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
	if (undefined !== oProbe.lastCode) {
		oRow.removeClass().addClass(this.oHelper.getRowClassByCode(oProbe.lastCode));
	        oRow.find('.code span').html(oProbe.lastCode).removeClass().addClass('badge').addClass(this.oHelper.getBadgeClassByCode(oProbe.lastCode));
        	oRow.find('.lastMessage strong').html(oProbe.lastMessage);
	        var iAppNb = oProbe.lastApplications.length;
        	if (0 < iAppNb) {
                	var sAppContent = '';
	                for (var i = 0; i < oProbe.lastApplications.length; i++) {
        	                var sAppName = oProbe.lastApplications[i].name;
                	        var iAppCode = oProbe.lastApplications[i].code;
                        	var sAppHtml = '<span class="badge '+this.oHelper.getBadgeClassByCode(iAppCode)+'">'+sAppName+'</span>&nbsp;';
	                        sAppContent += sAppHtml;
        	        }
        	        oRow.find('.application').html(sAppContent);
	        }
	}
	oRow.find('.lastCheck').html(oProbe.lastCheckFormated);
};



Updater.prototype.updateClientNumber = function(iNumber) {
	var oClientNode = $('#nbClient');
	oClientNode.html(iNumber);	
}

oUpdater = new Updater();
oUpdater.start();
