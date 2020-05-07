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

if (SENTRY){
	SENTRY = `
	<script src="https://browser.sentry-cdn.com/5.15.5/bundle.min.js" integrity="sha384-wF7Jc4ZlWVxe/L8Ji3hOIBeTgo/HwFuaeEfjGmS3EXAG7Y+7Kjjr91gJpJtr+PAT" crossorigin="anonymous">
	</script>
	<script>Sentry.init({ dsn: "`+SENTRY+`" });</script>`;
}

if (GOOGLE_ANALYTICS){
	GOOGLE_ANALYTICS = `
	<script async src="https://www.googletagmanager.com/gtag/js?id=`+GOOGLE_ANALYTICS+`"></script>
	<script>
		window.dataLayer = window.dataLayer || [];
		function gtag(){dataLayer.push(arguments);}
		gtag('js', new Date());
		gtag('config', "`+GOOGLE_ANALYTICS+`");
	</script>`;
}

if (FULLSTORY){
	FULLSTORY = `
	<script>
		window['_fs_debug'] = false;
		window['_fs_host'] = 'fullstory.com';
		window['_fs_script'] = 'edge.fullstory.com/s/fs.js';
		window['_fs_org'] = "`+FULLSTORY+`";
		window['_fs_namespace'] = 'FS';
		(function(m,n,e,t,l,o,g,y){
			if (e in m) {if(m.console && m.console.log) { m.console.log('FullStory namespace conflict. Please set window["_fs_namespace"].');} return;}
			g=m[e]=function(a,b,s){g.q?g.q.push([a,b,s]):g._api(a,b,s);};g.q=[];
			o=n.createElement(t);o.async=1;o.crossOrigin='anonymous';o.src='https://'+_fs_script;
			y=n.getElementsByTagName(t)[0];y.parentNode.insertBefore(o,y);
			g.identify=function(i,v,s){g(l,{uid:i},s);if(v)g(l,v,s)};g.setUserVars=function(v,s){g(l,v,s)};g.event=function(i,v,s){g('event',{n:i,p:v},s)};
			g.anonymize=function(){g.identify(!!0)};
			g.shutdown=function(){g("rec",!1)};g.restart=function(){g("rec",!0)};
			g.log = function(a,b){g("log",[a,b])};
			g.consent=function(a){g("consent",!arguments.length||a)};
			g.identifyAccount=function(i,v){o='account';v=v||{};v.acctId=i;g(o,v)};
			g.clearUserCookie=function(){};
			g._w={};y='XMLHttpRequest';g._w[y]=m[y];y='fetch';g._w[y]=m[y];
			if(m[y])m[y]=function(){return g._w[y].apply(this,arguments)};
			g._v="1.2.0";
		})(window,document,window['_fs_namespace'],'script','user');
	</script>`;
}
