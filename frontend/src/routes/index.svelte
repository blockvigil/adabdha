<script>
	import { goto } from '@sapper/app';
	import { onMount, onDestroy, tick } from 'svelte';
	import { unlockAccount, checkAccount, mainAPI } from '../common.js';
	import { account } from '../stores.js';
	import KYC from '../components/KYC.svelte';

	let requestedOTP = false;
	let submittedOTP = false;
	let email = '';
	let ethAddress = '';
	let otp = ['', '', '', '', '', ''];
	let jsonStore = null;
	let validEmail = false;

	let showSubmitOTPButton = false;
	let showButtonLoader = false;

	const requestOTP = async () => {
		validEmail = false;
		showButtonLoader = true;
		/*
		const response = await mainAPI.get('/users');
		for (let i=0; i<response.data.length; i++){
			if (response.data[i].email == email){
				validEmail = true;
				alert("Email exists!");
				return;
			}
		}
		*/

		const data = {"email": email, "ethAddress": await unlockAccount()};
		mainAPI.post('/users/', data).then((d) => {
			requestedOTP = true;
			ethAddress = d.data.ethAddress;
			console.log(d.data);
			showButtonLoader = false;
		}).catch((error) => {
			validEmail = true;
			showButtonLoader = false;
			alert("Something went wrong!");
			console.error(error);
		});
	}

	const submitOTP = async () => {
		showSubmitOTPButton = false;
		showButtonLoader = true;
		const data = {"email": email, "otp": otp.join("")};
		mainAPI.put('/user/'+ethAddress, {otp: data.otp}).then((d) => {
			submittedOTP = true;
			console.log(d.data);
			account.set({email: email, ethAddress: ethAddress, kycVerified: "unverified", otpVerified: true});
			localStorage.setItem('adabdha_user', JSON.stringify({ethAddress: ethAddress}))
		}).catch((error) => {
			showSubmitOTPButton = true;
			showButtonLoader = false;
			alert("Something went wrong!");
			console.error(error);
		});
	}


	$: {
		let flag = false;
		for (let i=0; i<6; i++){
			if (otp[i] == ''){
				flag = true;
				showSubmitOTPButton = false;
				break;
			}
		}
		if (!flag){
			showSubmitOTPButton = true;
		}

		if (/^[a-zA-Z0-9.!#$%&’*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$/.test(email)){
			validEmail = true;
		} else {
			validEmail = false;
		}
	}

	onMount(async () => {
		jsonStore = localStorage.getItem('jsonStore');
		if (jsonStore){
			//await unlockAccount();
		}
		if (await checkAccount() && ($account.kycVerified == 'pending' || $account.kycVerified == 'requested')){
			mainAPI.get('/user/'+$account.ethAddress).then((d) => {
				d = d.data;
				if ($account.godMode){
					d.godMode = true;
				}
				account.set(d);
				console.log('account is now', $account);
			})
		}
	});

</script>

<div class="rounded-md bg-blue-50 p-2">
	<div class="flex">
		<div class="flex-shrink-0">
			<svg class="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
				<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
			</svg>
		</div>
		<div class="ml-3 flex-1 md:flex md:justify-between">
			<p class="text-sm leading-5 text-blue-700">
				This is a demo hosted by BlockVigil. No forms or passes are considered valid by any authorities. If you like it, please reach out to your local govt to work with us to integrate the project.
			</p>
		</div>
	</div>
	<div> </div>
</div>

<div class="sm:mx-auto sm:w-full sm:max-w-md">
	<h2 class="mt-4 text-center text-3xl leading-9 font-extrabold text-gray-900">
		Adabdha Pass
	</h2>
</div>

{#if !$account || submittedOTP}

<div class="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
	<div class="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
		{#if !requestedOTP}
		<div>
			<label for="email" class="block text-sm font-medium leading-5 text-gray-700">Email</label>
			<div class="mt-1 relative rounded-md shadow-sm">
				<div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
				<svg class="h-5 w-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
					<path fill-rule="evenodd" d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884zM18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z" clip-rule="evenodd"/>
				</svg>
				</div>
				<input type="email" name="email" bind:value={email} class="validate form-input block w-full pl-10 sm:text-sm sm:leading-5" placeholder="Enter your email address" />
			</div>
		</div>
		<div class="mt-6">
			<span class="block w-full rounded-md shadow-sm">
			{#if validEmail}
				<button type="submit" class="w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-500 focus:outline-none focus:border-indigo-700 focus:shadow-outline-indigo active:bg-indigo-700 transition duration-150 ease-in-out" on:click={requestOTP}>
				Request OTP
				</button>
			{:else}
				<button type="submit" class="opacity-50 cursor-not-allowed w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-500 focus:outline-none focus:border-indigo-700 focus:shadow-outline-indigo active:bg-indigo-700 transition duration-150 ease-in-out">
				{#if showButtonLoader}
				Requesting OTP <div class="lds-ring"><div></div><div></div><div></div><div></div></div>
				{:else}
				Request OTP
				{/if}
				</button>
			{/if}
			</span>
		</div>
		{:else}
			{#if !submittedOTP}
			<div class="mt-1 pt-1">
				<div>
					<h3 class="text-lg leading-6 font-medium text-gray-900">
						Enter OTP
					</h3>
					<p class="mt-1 text-sm leading-5 text-gray-500">
						Sent to {email}
					</p>
				</div>
			</div>
			<div class="mt-4 pt-4">
				<div class="-mt-px flex">
					{#each otp as v, i}
						<div class="pr-1 w-1/6 flex-1 min-w-0">
							<input type="text" id="otp{i}" on:keyup={(e) => {
								if (e.keyCode == 8){
									if (i>0){
										document.getElementById('otp'+(i-1)).focus();
									}
								} else {
									if (isNaN(otp[i])){
										otp[i] = '';
									}
									if (otp[i] != '' && i<5){
										document.getElementById('otp'+(i+1)).focus();
									}
								}
								}} on:paste={(e) => {
									var clipboardData, pastedData;
									e.stopPropagation();
									e.preventDefault();
									clipboardData = e.clipboardData || window.clipboardData;
									pastedData = clipboardData.getData('Text').trim();
									for (let i=0; i<6; i++){
										if (isNaN(pastedData[i])){
											break;
										}
										otp[i] = pastedData[i];
										if (i<5){
											document.getElementById('otp'+(i+1)).focus();
										}
									}
								}}
								bind:value={otp[i]} maxlength="1" class="validate form-input block w-full pl-5 sm:text-sm sm:leading-5" placeholder=0 />
						</div>
					{/each}
				</div>
			</div>
			<div class="mt-6">
				<span class="block w-full rounded-md shadow-sm">
				{#if showSubmitOTPButton}
					<button type="submit" class="w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-500 focus:outline-none focus:border-indigo-700 focus:shadow-outline-indigo active:bg-indigo-700 transition duration-150 ease-in-out" on:click={submitOTP}>
					Submit OTP
					</button>
				{:else}
					<button type="submit" class="opacity-50 cursor-not-allowed w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-500 focus:outline-none focus:border-indigo-700 focus:shadow-outline-indigo active:bg-indigo-700 transition duration-150 ease-in-out">
					{#if showButtonLoader}
					Submitting OTP <div class="lds-ring"><div></div><div></div><div></div><div></div></div>
					{:else}
					Submit OTP
					{/if}
					</button>
				{/if}
				</span>
			</div>
			{:else}
			<div class="bg-gray-50 sm:rounded-lg">
				<div class="px-4 py-5 sm:p-6">
					<h3 class="text-lg leading-6 font-medium text-gray-900">
						OTP confirmed!
					</h3>
					<div class="mt-5">
						<span class="inline-flex rounded-md shadow-sm">
							<button type="button" on:click={() => {goto('/forms/new')}} class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm leading-5 font-medium rounded-md text-gray-700 bg-white hover:text-gray-500 focus:outline-none focus:border-blue-300 focus:shadow-outline-blue active:text-gray-800 active:bg-gray-50 transition ease-in-out duration-150">
								Fill Form
							</button>
						</span>
					</div>
				</div>
			</div>
			{/if}
		{/if}
	</div>
</div>

{:else}
<div class="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
	<div class="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
	{#if $account.email}
		Hello {$account.email}
	{:else}
		Loading..
	{/if}
	</div>
</div>
	{#if $account.kycVerified != undefined }
	<div class="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
		<div class="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
			KYC status: <KYC />
		</div>
	</div>
	{/if}
{/if}
