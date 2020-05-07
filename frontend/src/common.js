import axios from 'axios';
import { account, wsTxStore } from './stores.js';

export const API_PREFIX = process.env.API_PREFIX;
let wsURL = process.env.WS_URL;
let wsKey = process.env.WS_KEY;
export let godModeApproval = process.env.GOD_MODE_APPROVAL === true;

export let SENTRY = process.env.SENTRY;
export let FULLSTORY = process.env.FULLSTORY;
export let GOOGLE_ANALYTICS = process.env.GOOGLE_ANALYTICS;

let wsConnection, wsSessionID;
let wsTries = 5;
let timeout = 1000;
let instance;

export const mainAPI = axios.create({
	baseURL: API_PREFIX,
	timeout: 5000
});

let account_value;
const unsubscribeAccount = account.subscribe(value => {
	account_value = value;
});

mainAPI.interceptors.request.use(async function (config) {
	await unlockAccount();
	const timestamp = parseInt(+new Date()/1000);
	const msg = 'adabdha_'+timestamp;
	config.headers = {'X-Wallet-Signature': msg+':'+walletSign(msg)};
	return config;
}, function (error) {
	//console.error('request error?', error);
	return Promise.reject(error);
});

function walletSign(msg){
	const sig = sigUtil.personalSign(instance.getPrivateKey(), {data: msg});
	return sig;
}

export const checkAccount = async () => {
	if (account_value){
		return true;
	}
	try {
		const user = JSON.parse(localStorage.getItem('adabdha_user'));
		if (user.ethAddress){
			account.set(user);
			let response = await mainAPI.get('/user/'+user.ethAddress);
			account.set(response.data);
			initWS();
			if (typeof(FS) != 'undefined'){
				FS.identify(user.ethAddress, {
					email: response.data.email
				});
			}
			return true;
		} else {
			return false;
		}
	}
	catch (e){
		return false;
	}
}

export const unlockAccount = () => {
	if (instance){
		const address = instance.getChecksumAddressString().toLowerCase();
		if (typeof(FS) != 'undefined'){
			FS.identify(address);
		}
		return address;
	}
	var jsonStore = localStorage.getItem('jsonStore');
	const p = new Promise(function(presolve, preject) {
		if (jsonStore){
			console.warn('Unlocking wallet...');
			var loading = new Promise(function(resolve, reject) {
				setTimeout(function() {
					try {
						instance= ethWallet.fromV3(jsonStore, "test123");
						resolve();
					}
					catch (e){
						alert('Wrong Password!');
					}
				}, 300);
			});
			loading.then(function() {
				var address = instance.getChecksumAddressString().toLowerCase();
				console.log('unlocked', address);
				presolve(address);
			});
		} else {
			console.log('generating wallet');
			instance = ethWallet.generate();
			var generating = new Promise(function(resolve, reject) {
				setTimeout(function() {
					try {
						jsonStore = instance.toV3("test123", {
							kdf: "pbkdf2"
						});
						resolve();
					}
					catch (e){
						alert('Wrong Password!');
					}
				}, 300);
			});
			generating.then(function() {
				var address = instance.getChecksumAddressString().toLowerCase();
				console.log('generated', address);
				localStorage.setItem('jsonStore', JSON.stringify(jsonStore));
				presolve(address);
			});
		}
	});
	return p;
}

export function initWS(){
	if (wsTries <= 0){
		console.error('unable to estabilish WS after 5 tries!');
		wsConnection = null;
		wsTries = 5;
		wsSessionID = null;
		return;
	}
	//Don't open a new websocket if it already exists. Figure out a better way for event filtering #FIXME
	if (wsConnection){
		return;
	}
	wsConnection = new WebSocket(wsURL);
	wsConnection.onopen = function () {
		wsConnection.send(JSON.stringify({
			'command': 'register',
			'key': wsKey
		}));
		setTimeout(heartbeat, 30000);
	};

	// Log errors
	wsConnection.onerror = function (error) {
		wsTries--;
		console.error('WebSocket Error ', error);
	};

	// Log messages from the server
	wsConnection.onmessage = function (d) {
		try {
			var data = JSON.parse(d.data);
			if (data.command){
				if (data.command == 'register:nack'){
					console.error('bad auth from WS');
					closeWS();
				}
				if (data.command == 'register:ack'){
					console.log('got WS session', data.sessionID);
					wsSessionID = data.sessionID;
				}
				return;
			}
			if (data.type == 'event'){
				wsTxStore.set({data: data.event_data, name: data.event_name});
			}
		}
		catch (e){
			console.error('got non json data', d.data, e);
		}
	};
	wsConnection.onclose = function(e){
		if (e.code != 1000){
			closeWS();
		} else {
			setTimeout(function(){
				initWS();
			}, timeout);
		}
	};
}

export function closeWS(){
	if (wsConnection){
		wsSessionID = null;
		wsConnection.onclose = function(){
			wsConnection = null;
		};
		wsConnection.close();
	}
}

function heartbeat() {
	if (!wsSessionID || !wsConnection || wsConnection.readyState !== 1){
		return;
	}
	wsConnection.send(JSON.stringify({
		command: "heartbeat",
		sessionID: wsSessionID
	}));
	setTimeout(heartbeat, 30000);
}
