var hash;
var eth, contract;
var contractABI = [{"inputs":[],"payable":false,"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"bytes32","name":"uuidHash","type":"bytes32"},{"indexed":true,"internalType":"address","name":"ethAddress","type":"address"}],"name":"FormApproved","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"bytes32","name":"uuidHash","type":"bytes32"},{"indexed":true,"internalType":"address","name":"ethAddress","type":"address"}],"name":"FormRejected","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"bytes32","name":"uuidHash","type":"bytes32"},{"indexed":true,"internalType":"address","name":"ethAddress","type":"address"},{"indexed":false,"internalType":"bytes32","name":"formdataHash","type":"bytes32"}],"name":"NewForm","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"bytes32","name":"passDataHash","type":"bytes32"},{"indexed":false,"internalType":"address","name":"ethAddress","type":"address"},{"indexed":false,"internalType":"bytes32","name":"formUUIDHash","type":"bytes32"}],"name":"PassGenerated","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"bytes32","name":"passDataHash","type":"bytes32"},{"indexed":false,"internalType":"address","name":"ethAddress","type":"address"},{"indexed":false,"internalType":"bytes32","name":"formUUIDHash","type":"bytes32"}],"name":"PassRevoked","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"ethAddress","type":"address"},{"indexed":false,"internalType":"enum AdabdhaMain.UserStates","name":"status","type":"uint8"}],"name":"UserStatusUpdated","type":"event"},{"constant":false,"inputs":[{"internalType":"address","name":"ethAddress","type":"address"},{"internalType":"bytes32","name":"emailHash","type":"bytes32"}],"name":"addUserByEmail","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"ethAddress","type":"address"},{"internalType":"bytes32","name":"phoneHash","type":"bytes32"}],"name":"addUserByPhone","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"oracle","type":"address"}],"name":"addUserRegistrationOracle","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"bytes32","name":"uuidHash","type":"bytes32"}],"name":"approveForm","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"ethAddress","type":"address"},{"internalType":"bytes32","name":"formUUIDHash","type":"bytes32"},{"internalType":"bytes32","name":"passHash","type":"bytes32"}],"name":"generatePass","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"internalType":"int8","name":"statusCode","type":"int8"}],"name":"getFormStateIdentifierByCode","outputs":[{"internalType":"string","name":"statusIdentifier","type":"string"}],"payable":false,"stateMutability":"pure","type":"function"},{"constant":true,"inputs":[{"internalType":"bytes32","name":"uuidHash","type":"bytes32"}],"name":"getFormStatus","outputs":[{"internalType":"int8","name":"status","type":"int8"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"string","name":"statusIdentifier","type":"string"}],"name":"getFormStatusCodeByIdentifier","outputs":[{"internalType":"int8","name":"statusCode","type":"int8"}],"payable":false,"stateMutability":"pure","type":"function"},{"constant":true,"inputs":[{"internalType":"bytes32","name":"passDataHash","type":"bytes32"}],"name":"getPass","outputs":[{"internalType":"address","name":"ethAddress","type":"address"},{"internalType":"bytes32","name":"formUUIDHash","type":"bytes32"},{"internalType":"uint256","name":"timestamp","type":"uint256"},{"internalType":"bool","name":"status","type":"bool"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"lastApplicationId","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"name":"passInformation","outputs":[{"internalType":"address","name":"ethAddress","type":"address"},{"internalType":"bytes32","name":"formUUIDHash","type":"bytes32"},{"internalType":"uint256","name":"createdTimestamp","type":"uint256"},{"internalType":"bool","name":"status","type":"bool"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"bytes32","name":"uuidHash","type":"bytes32"}],"name":"rejectForm","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"bytes32","name":"passDataHash","type":"bytes32"}],"name":"revokePass","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"ethAddress","type":"address"}],"name":"revokeUser","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"bytes32","name":"uuidHash","type":"bytes32"},{"internalType":"address","name":"ethAddress","type":"address"},{"internalType":"bytes32","name":"formdataHash","type":"bytes32"}],"name":"submitFormData","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"ethAddress","type":"address"}],"name":"submitUserKYCVerification","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"internalType":"uint256","name":"","type":"uint256"}],"name":"userDataOracles","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"userExists","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"userInformation","outputs":[{"internalType":"bytes32","name":"emailHash","type":"bytes32"},{"internalType":"bytes32","name":"phoneHash","type":"bytes32"},{"internalType":"bytes32","name":"passDataHash","type":"bytes32"},{"internalType":"enum AdabdhaMain.UserStates","name":"status","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"}];

var video = document.createElement("video");
var canvasElement = document.getElementById("canvas");
var canvas = canvasElement.getContext("2d");
var loadingMessage = document.getElementById("loadingMessage");
var outputContainer = document.getElementById("output");
var outputMessage = document.getElementById("outputMessage");
var outputData = document.getElementById("outputData");

function drawLine(begin, end, color) {
	canvas.beginPath();
	canvas.moveTo(begin.x, begin.y);
	canvas.lineTo(end.x, end.y);
	canvas.lineWidth = 4;
	canvas.strokeStyle = color;
	canvas.stroke();
}

function startScan(){
	$("#view").show();
	$("#scanbutton").hide();
	$("#uploadbox").hide();
	// Use facingMode: environment to attemt to get the front camera on phones
	navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } }).then(function(stream) {
		video.srcObject = stream;
		video.setAttribute("id", "video"); // required to tell iOS safari we don't want fullscreen
		video.setAttribute("playsinline", true); // required to tell iOS safari we don't want fullscreen
		video.play();
		requestAnimationFrame(tick);
	});
}



function tick() {
	loadingMessage.innerText = "⌛ Loading video..."
	if (video.readyState === video.HAVE_ENOUGH_DATA) {
		loadingMessage.hidden = true;
		canvasElement.hidden = false;
		outputContainer.hidden = false;

		canvasElement.height = video.videoHeight;
		canvasElement.width = video.videoWidth;
		canvas.drawImage(video, 0, 0, canvasElement.width, canvasElement.height);
		var imageData = canvas.getImageData(0, 0, canvasElement.width, canvasElement.height);
		var code = jsQR(imageData.data, imageData.width, imageData.height, {
			inversionAttempts: "dontInvert",
		});
		if (code) {
			video.srcObject.getTracks().forEach(function(track) {
				track.stop();
			});
			//video.stop();
			drawLine(code.location.topLeftCorner, code.location.topRightCorner, "#FF3B58");
			drawLine(code.location.topRightCorner, code.location.bottomRightCorner, "#FF3B58");
			drawLine(code.location.bottomRightCorner, code.location.bottomLeftCorner, "#FF3B58");
			drawLine(code.location.bottomLeftCorner, code.location.topLeftCorner, "#FF3B58");
			outputMessage.hidden = true;
			$("#view").hide();
			$("#loadingProof").show();
			$("#scanbutton").show();
			processData(code.data);
		} else {
			//outputMessage.hidden = false;
			//outputData.parentElement.hidden = true;
		}
	}
	requestAnimationFrame(tick);
}

$(document).ready(function(){
	// If web3 is not injected (modern browsers)...
	if (typeof web3 === 'undefined') {
		// Listen for provider injection
		window.addEventListener('message', function(data) {
			if (data && data.type && data.type === 'ETHEREUM_PROVIDER_SUCCESS') {
				// Use injected provider, start dapp...
				eth = new Eth(ethereum);
			}
		});
		// Request provider
		window.postMessage({ type: 'ETHEREUM_PROVIDER_REQUEST' }, '*');
	}
	// If web3 is injected (legacy browsers)...
	else {
		// Use injected provider, start dapp
		eth = new Eth(web3.currentProvider);
	}
});

function processData(data){
	hash = keccak256(data);
	try {
		data = JSON.parse(data);
	}
	catch (e){
		console.error('bad json');
		$("#loadingProof").hide();
		alert('Bad QR code. Try again!');
		return;
	}
	const API_PREFIX = data.api_prefix || 'https://beta-api.ethvigil.com/v0.1/contract/0x5e1ddb58ad3a695750984fab3de5a876045a1410';
	data.ethvigil_paths = data.api_prefix.split('/');
	var prefix = "https://etherscan.io";
	var network = {
		id: 1,
		name: "Main"
	};
	switch (data.ethvigil_paths[2]){
		case "localhost:8080":
			prefix = "http://localhost:8282";
			network = {
				id: 8997,
				name: "Custom"
			}
		break;
		case "beta-api.ethvigil.com":
			prefix = "https://goerli.etherscan.io";
			network = {
				id: 5,
				name: "Goerli"
			}
		break;
		case "mainnet-api.ethvigil.com":
			prefix = "https://etherscan.io";
			network = {
				id: 1,
				name: "Mainnet"
			}
		break;
	}
	$("#etherscan").off().on('click', function(){
		window.open(prefix+'/address/'+data.ethvigil_paths[data.ethvigil_paths.length-1],'_blank');
	});
	if (eth){
		eth.net_version().then(function(d){
			if (d != network.id){
				//$(".box__input").show();
				//$("#loader").hide();
				console.warn("Please switch to "+network.name+" network in yout Metamask/Dapp browser for 100% proof. We will now use EthVigil API as a fallback for verification.")
				evFallback(data);
			} else {
				contract = eth.contract(contractABI).at(data.ethvigil_paths[data.ethvigil_paths.length-1]);
				contract.passInformation('0x'+hash).then(function(d){
					if (d.status){
						//alert('verified!');
						$("#loadingProof").hide();
						addDocumentInfo(data);
					} else {
						$("#loadingProof").hide();
						alert('revoked!');
					}
				});
			}
		});
	} else {
		evFallback(data);
	}
}

function evFallback(data){
	$.getJSON(data.api_prefix+'/passInformation/0x'+hash, function(d){
		if (d.data[0].status){
			//alert('verified!');
			$("#loadingProof").hide();
			addDocumentInfo(data);
		} else {
			$("#loadingProof").hide();
			alert('revoked!');
		}
	}).fail(function(d){
		$("#loadingProof").hide();
		alert('We had trouble checking the proof!');
		console.error(d.responseJSON);
	});
}

function addDocumentInfo(data){
	var body = "";
	for (i in data){
		if (i == parseInt(i)){
			continue;
		}
		if (!data[i] || i == 'api_prefix' || i == 'ethvigil_paths' || (i=='mock_data' && !data[i])){
			continue;
		}
		switch (i){
			case 'ctime':
				data[i] = timeDifference(data[i]*1000);
			break;
			case 'purpose':
				purposeString = "";
				for (let j in data[i]){
					if (data[i][j]){
						if (purposeString){
							purposeString += ', '+j;
						} else {
							purposeString = j;
						}
					}
				}
				data[i] = purposeString;
			break;
			case 'identity_document_type':
				var d = data[i];
				i = 'Identity';
				data[i] = d;
			break;
			case 'expiration_date':
			case 'dob':
			case 'address':
				data[i] = JSON.stringify(data[i]);
			break;
		}
		body += '<div class="sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6 sm:py-5"><dt class="text-sm leading-5 font-medium text-gray-500">'+i+'</dt><dd class="mt-1 text-sm leading-5 text-gray-900 sm:mt-0 sm:col-span-2">'+data[i]+'</dd></div>';
	}
	$("#loader").hide();
	$("#passBody").html(body);
	$("#modal").show();
	return true;
}

function showAlert(message, title){
	$("#alert p").text(message);
	if (!title){
		title = 'Error!';
	}
	$("#alert h4").text(title);
	$('#alert').modal("open");
}

function timeDifference(previous, current) {
	current = current ? current : +new Date();
	var msPerMinute = 60 * 1000;
	var msPerHour = msPerMinute * 60;
	var msPerDay = msPerHour * 24;
	var msPerMonth = msPerDay * 30;
	var msPerYear = msPerDay * 365;
	var v;
	var elapsed = current - previous;

	if (elapsed < msPerMinute) {
		v = Math.round(elapsed/1000);
		return v + ' second'+(v>1 ? 's' : '')+' ago';
	}

	else if (elapsed < msPerHour) {
		v = Math.round(elapsed/msPerMinute);
		return v + ' minute'+(v>1 ? 's' : '')+' ago';
	}

	else if (elapsed < msPerDay ) {
		v = Math.round(elapsed/msPerHour);
		return v + ' hour'+(v>1 ? 's' : '')+' ago';
	}

	else if (elapsed < msPerMonth) {
		v = Math.round(elapsed/msPerDay);
		return v + ' day'+(v>1 ? 's' : '')+' ago';
	}

	else if (elapsed < msPerYear) {
		v = Math.round(elapsed/msPerMonth);
		return v + ' month'+(v>1 ? 's' : '')+' ago';
	}

	else {
		v = Math.round(elapsed/msPerYear);
		return v + ' year'+(v>1 ? 's' : '')+' ago';
	}
}
