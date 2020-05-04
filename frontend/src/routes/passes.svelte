<script>
	import { goto } from '@sapper/app';
	import { onMount, onDestroy } from 'svelte';
	import { unlockAccount, checkAccount, mainAPI } from '../common.js';
	import { account } from '../stores.js';
	import { fly } from 'svelte/transition';
	import KYC from '../components/KYC.svelte';

	let passHashes = [];
	let passes = [];
	let loading = true;
	let passInfo = {};
	let formActionPending = false;
	let account_data = {};

	const unsubscribeAccount = account.subscribe(value => {
		if (value && value.godMode != account_data.godMode && !loading){
			account_data = value;
			loading = true;
			getPasses();
		}
	});

	onMount(async () => {
		if (await checkAccount()){
			getPasses();
		} else {
			goto('/');
		}
	});

	onDestroy(async () => {
		unsubscribeAccount();
	});

	let showPass = false;

	const cancelPass = async () => {
		console.log('canceling', passInfo.hash);
		formActionPending = true;
		mainAPI.post('/pass/'+passInfo.hash, {action: 'revoke'}).then((d) => {
			console.log(d.data);
			showPass = false;
		}).catch((error) => {
			alert("Something went wrong!");
			formActionPending = false;
			console.error(error);
		});
	}

	const openPass = async (hash) => {
		passInfo = JSON.stringify(passes[passHashes.indexOf(hash)].passData);
		QRCode.toDataURL(passInfo, function (error, url) {
			if (error){
				console.error(error)
				alert("Could not generated QR code for your pass!");
			} else {
				passInfo = JSON.parse(passInfo);
				passInfo.qr = url;
				passInfo.hash = hash;
				passInfo.status = passes[passHashes.indexOf(hash)].status;
				for (let j in passInfo.purpose){
					if (passInfo.purpose[j]){
						if (passInfo.purposeString){
							passInfo.purposeString += ', '+j;
						} else {
							passInfo.purposeString = j;
						}
					}
				}
				showPass = true;
			}
		})
	}

	const downloadQR = function(){
		let link = document.createElement('a');
		link.download = 'pass-'+passInfo.hash.substr(-5)+'.png';
		link.href = passInfo.qr;
		link.click();
	}

	const getPasses = async () => {
		passes = [];
		passHashes = [];
		try {
			const response = await mainAPI.get($account.godMode ? '/passes/' : '/user/'+$account.ethAddress+'/passes');
			for (let i=0; i<response.data.length; i++){
				const data = response.data[i];
				if (passHashes.indexOf(data.passDataHash) != -1){
					console.warn('duplicate', data.passDataHash);
					continue;
				}
				if (data.status){
					data.status = 'approved';
					data.statusColor = 'green';
				} else {
					data.status = 'revoked';
					data.statusColor = 'red';
				}
				for (let j in data.passData.purpose){
					if (data.passData.purpose[j]){
						if (data.purposeString){
							data.purposeString += ', '+j;
						} else {
							data.purposeString = j;
						}
					}
				}
				passHashes.push(data.passDataHash);
				passes = [...passes, data];
			}
			loading = false;
		}
		catch(e){
			console.error(e);
		}
	}
</script>

{#if loading}
	Loading passes...
{:else if passes.length == 0}
	{#if $account.kycVerified != 'verified'}
		<div class="rounded-md bg-yellow-50 p-4">
			<div class="flex">
				<div class="flex-shrink-0">
					<svg class="h-5 w-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
						<path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
					</svg>
				</div>
				<div class="ml-3">
					<h3 class="text-sm leading-5 font-medium text-yellow-800">
						{$account.kycVerified == 'pending' || $account.kycVerified =='requested' ? 'Passes will generate once KYC is processed' : 'You need to complete KYC to generate a pass!'}
					</h3>
					<div class="mt-2 text-sm leading-5 text-yellow-700">
						<KYC showStatus=false />
					</div>
				</div>
			</div>
		</div>
	{:else}
		<div class="rounded-md bg-blue-50 p-4">
			<div class="flex">
				<div class="flex-shrink-0">
					<svg class="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
						<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
					</svg>
				</div>
				<div class="ml-3 flex-1 md:flex md:justify-between">
					<p class="text-sm leading-5 text-blue-700">
						Passes will generate once forms get approved.
					</p>
					<p class="mt-3 text-sm leading-5 md:mt-0 md:ml-6">
						<a href="/forms" class="whitespace-no-wrap font-medium text-blue-700 hover:text-blue-600 transition ease-in-out duration-150">
							Forms &rarr;
						</a>
					</p>
				</div>
			</div>
		</div>
	{/if}
{/if}
<div class="mt-6 sm:mt-5">
	<div class="bg-white shadow overflow-hidden sm:rounded-md">
		<ul>
		{#each passes as pass}
			<li on:click={() => openPass(pass.passDataHash)} class="cursor-pointer block hover:bg-gray-50 focus:outline-none focus:bg-gray-50 transition duration-150 ease-in-out">
				<div class="px-4 py-4 sm:px-6">
					<div class="flex items-center justify-between">
						<div class="text-sm leading-5 font-medium text-indigo-600 truncate">
							{pass.passDataHash.substr(-5)} - {pass.passData.first_name} {pass.passData.last_name}
						</div>
						<div class="ml-2 flex-shrink-0 flex">
							<span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-{pass.statusColor}-100 text-{pass.statusColor}-800">
								{pass.status}
							</span>
						</div>
					</div>
					<div class="mt-2 sm:flex sm:justify-between">
						<div class="sm:flex">
							<div class="mr-6 flex items-center text-sm leading-5 text-gray-500 capitalize">
							<svg class="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
								<path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z"/>
							</svg>
							{pass.purposeString}
							</div>
							<div class="mt-2 flex items-center text-sm leading-5 text-gray-500 sm:mt-0 capitalize">
							<svg class="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
								<path fill-rule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd"/>
							</svg>
							Within {pass.passData.movement}
							</div>
						</div>
						<div class="mt-2 flex items-center text-sm leading-5 text-gray-500 sm:mt-0">
							<svg class="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
							<path fill-rule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clip-rule="evenodd"/>
							</svg>
							<span>
							<time datetime={new Date(pass.timestamp*1000)}>{new Date(pass.timestamp*1000)}</time>
							</span>
						</div>
					</div>
				</div>
			</li>
		{/each}
		</ul>
	</div>
</div>

{#if showPass}
{#if !$account.godMode}
{#if passInfo.status == 'approved'}
<div x-show="open" class="fixed bottom-0 inset-x-0 px-4 pb-6 sm:inset-0 sm:p-0 sm:flex sm:items-center sm:justify-center">
	<div x-show="open" x-transition:enter="ease-out duration-300" x-transition:enter-start="opacity-0" x-transition:enter-end="opacity-100" x-transition:leave="ease-in duration-200" x-transition:leave-start="opacity-100" x-transition:leave-end="opacity-0" class="fixed inset-0 transition-opacity">
		<div class="absolute inset-0 bg-gray-500 opacity-75"></div>
	</div>

	<div x-show="open" x-transition:enter="ease-out duration-300" x-transition:enter-start="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95" x-transition:enter-end="opacity-100 translate-y-0 sm:scale-100" x-transition:leave="ease-in duration-200" x-transition:leave-start="opacity-100 translate-y-0 sm:scale-100" x-transition:leave-end="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95" class="bg-white rounded-lg px-4 pt-5 pb-4 overflow-hidden shadow-xl transform transition-all sm:max-w-sm sm:w-full sm:p-6">
		<div>
			<div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
				<svg class="h-6 w-6 text-green-600" stroke="currentColor" fill="none" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
				</svg>
			</div>
			<div class="mt-3 text-center sm:mt-5">
				<i class="text-lg leading-6 font-medium text-gray-900">
					<a href="https://adabdha.com/proof.html" target="_blank">(Verify Proof)</a>
				</i>
				<div class="mt-2">
					<div class="bg-white shadow overflow-hidden	sm:rounded-lg">
						<div class="px-4 py-5 border-b border-gray-200 sm:px-6">
							<h3 class="text-lg leading-6 font-medium text-gray-900">
								Pass Info
							</h3>
							{passInfo.mock_data ? ' (CONTAINS MOCK DATA)': ''}
						</div>
						<div class="capitalize px-4 py-5 sm:p-0">
							<dl>
								<div class="sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6 sm:py-5">
									<dt class="text-sm leading-5 font-medium text-gray-500">
										Full name
									</dt>
									<dd class="mt-1 text-sm leading-5 text-gray-900 sm:mt-0 sm:col-span-2">
										{passInfo.first_name} {passInfo.last_name}
									</dd>
								</div>
							<div class="mt-8 sm:mt-0 sm:grid sm:grid-cols-3 sm:gap-4 sm:border-t sm:border-gray-200 sm:px-6 sm:py-5">
									<dt class="text-sm leading-5 font-medium text-gray-500">
										Identity
									</dt>
									<dd class="mt-1 text-sm leading-5 text-gray-900 sm:mt-0 sm:col-span-2">
										{passInfo.identity_document_type}
									</dd>
								</div>
								<div class="mt-8 sm:mt-0 sm:grid sm:grid-cols-3 sm:gap-4 sm:border-t sm:border-gray-200 sm:px-6 sm:py-5">
									<dt class="text-sm leading-5 font-medium text-gray-500">
										Purpose
									</dt>
									<dd class="mt-1 text-sm leading-5 text-gray-900 sm:mt-0 sm:col-span-2">
										{passInfo.purposeString}
									</dd>
								</div>
								<div class="mt-8 sm:mt-0 sm:grid sm:grid-cols-3 sm:gap-4 sm:border-t sm:border-gray-200 sm:px-6 sm:py-5">
									<dt class="text-sm leading-5 font-medium text-gray-500">
										Location
									</dt>
									<dd class="mt-1 text-sm leading-5 text-gray-900 sm:mt-0 sm:col-span-2">
										{passInfo.city}, {passInfo.state}
									</dd>
								</div>
								<div class="mt-8 sm:mt-0 sm:grid sm:grid-cols-3 sm:gap-4 sm:border-t sm:border-gray-200 sm:px-6 sm:py-5">
									<dt class="text-sm leading-5 font-medium text-gray-500">
										Movement
									</dt>
									<dd class="mt-1 text-sm leading-5 text-gray-900 sm:mt-0 sm:col-span-2">
										Within {passInfo.movement}
									</dd>
								</div>
								<div class="mt-8 sm:mt-0 sm:grid sm:grid-cols-3 sm:gap-4 sm:border-t sm:border-gray-200 sm:px-6 sm:py-5">
									<dt class="text-sm leading-5 font-medium text-gray-500">
										QR
									</dt>
									<dd class="mt-1 text-sm leading-5 text-gray-900 sm:mt-0 sm:col-span-2">
										<img src={passInfo.qr} alt="Pass QR Code" />
										<button type="button" on:click={downloadQR} class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm leading-5 font-medium rounded-md text-gray-700 bg-white hover:text-gray-500 focus:outline-none focus:border-blue-300 focus:shadow-outline-blue active:text-gray-800 active:bg-gray-50 transition ease-in-out duration-150">
											Download
										</button>
									</dd>
								</div>
							</dl>
						</div>
					</div>
				</div>
			</div>
		</div>
		<div class="mt-5 sm:mt-6">
			<span class="flex w-full rounded-md shadow-sm">
				<button type="button" on:click={() => {showPass = false;}} class="inline-flex justify-center w-full rounded-md border border-transparent px-4 py-2 bg-indigo-600 text-base leading-6 font-medium text-white shadow-sm hover:bg-indigo-500 focus:outline-none focus:border-indigo-700 focus:shadow-outline-indigo transition ease-in-out duration-150 sm:text-sm sm:leading-5">
					Close
				</button>
			</span>
		</div>
	</div>
</div>
{:else}
<div class="fixed bottom-0 inset-x-0 px-4 pb-4 sm:inset-0 sm:flex sm:items-center sm:justify-center">
	<!--
		Background overlay, show/hide based on modal state.

		Entering: "ease-out duration-300"
			From: "opacity-0"
			To: "opacity-100"
		Leaving: "ease-in duration-200"
			From: "opacity-100"
			To: "opacity-0"
	-->
	<div class="fixed inset-0 transition-opacity">
		<div class="absolute inset-0 bg-gray-500 opacity-75"></div>
	</div>

	<!--
		Modal panel, show/hide based on modal state.

		Entering: "ease-out duration-300"
			From: "opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
			To: "opacity-100 translate-y-0 sm:scale-100"
		Leaving: "ease-in duration-200"
			From: "opacity-100 translate-y-0 sm:scale-100"
			To: "opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
	-->
	<div class="relative bg-white rounded-lg px-4 pt-5 pb-4 overflow-hidden shadow-xl transform transition-all sm:max-w-lg sm:w-full sm:p-6">
		<div class="hidden sm:block absolute top-0 right-0 pt-4 pr-4">
			<button type="button" class="text-gray-400 hover:text-gray-500 focus:outline-none focus:text-gray-500 transition ease-in-out duration-150">
				<svg class="h-6 w-6" stroke="currentColor" fill="none" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
				</svg>
			</button>
		</div>
		<div class="sm:flex sm:items-start">
			<div class="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-red-100 sm:mx-0 sm:h-10 sm:w-10">
				<svg class="h-6 w-6 text-red-600" stroke="currentColor" fill="none" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
				</svg>
			</div>
			<div class="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
				<h3 class="text-lg leading-6 font-medium text-gray-900">
					Revoked pass
				</h3>
				<div class="mt-2">
					<p class="text-sm leading-5 text-gray-500">
						This pass has been revoked.
					</p>
				</div>
			</div>
		</div>
		<div class="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
			<span class="mt-3 flex w-full rounded-md shadow-sm sm:mt-0 sm:w-auto">
				<button type="button" on:click={() => {showPass = false;}} class="inline-flex justify-center w-full rounded-md border border-gray-300 px-4 py-2 bg-white text-base leading-6 font-medium text-gray-700 shadow-sm hover:text-gray-500 focus:outline-none focus:border-blue-300 focus:shadow-outline transition ease-in-out duration-150 sm:text-sm sm:leading-5">
					Close
				</button>
			</span>
		</div>
	</div>
</div>
{/if}
{:else}
<div class="fixed bottom-0 inset-x-0 px-4 pb-4 sm:inset-0 sm:flex sm:items-center sm:justify-center">
	<!--
		Background overlay, show/hide based on modal state.

		Entering: "ease-out duration-300"
			From: "opacity-0"
			To: "opacity-100"
		Leaving: "ease-in duration-200"
			From: "opacity-100"
			To: "opacity-0"
	-->
	<div class="fixed inset-0 transition-opacity">
		<div class="absolute inset-0 bg-gray-500 opacity-75"></div>
	</div>

	<!--
		Modal panel, show/hide based on modal state.

		Entering: "ease-out duration-300"
			From: "opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
			To: "opacity-100 translate-y-0 sm:scale-100"
		Leaving: "ease-in duration-200"
			From: "opacity-100 translate-y-0 sm:scale-100"
			To: "opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
	-->
	<div class="relative bg-white rounded-lg px-4 pt-5 pb-4 overflow-hidden shadow-xl transform transition-all sm:max-w-lg sm:w-full sm:p-6">
		<div class="hidden sm:block absolute top-0 right-0 pt-4 pr-4">
			<button type="button" class="text-gray-400 hover:text-gray-500 focus:outline-none focus:text-gray-500 transition ease-in-out duration-150">
				<svg class="h-6 w-6" stroke="currentColor" fill="none" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
				</svg>
			</button>
		</div>
		<div class="sm:flex sm:items-start">
			<div class="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-red-100 sm:mx-0 sm:h-10 sm:w-10">
				<svg class="h-6 w-6 text-red-600" stroke="currentColor" fill="none" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
				</svg>
			</div>
			<div class="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
				<h3 class="text-lg leading-6 font-medium text-gray-900">
					Revoke pass
				</h3>
				<div class="mt-2">
					<p class="text-sm leading-5 text-gray-500">
						Are you sure you want to revoke this pass? This action cannot be undone.
					</p>
				</div>
			</div>
		</div>
		<div class="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
			<span class="inline-flex rounded-md shadow-sm {formActionPending ? 'opacity-50 cursor-not-allowed' : ''}">
				<button type="button" on:click={cancelPass} class="inline-flex justify-center w-full rounded-md border border-transparent px-4 py-2 bg-red-600 text-base leading-6 font-medium text-white shadow-sm hover:bg-red-500 focus:outline-none focus:border-red-700 focus:shadow-outline-red transition ease-in-out duration-150 sm:text-sm sm:leading-5">
					Revoke
				</button>
			</span>
			<span class="mt-3 flex w-full rounded-md shadow-sm sm:mt-0 sm:w-auto">
				<button type="button" on:click={() => {showPass = false;}} class="inline-flex justify-center w-full rounded-md border border-gray-300 px-4 py-2 bg-white text-base leading-6 font-medium text-gray-700 shadow-sm hover:text-gray-500 focus:outline-none focus:border-blue-300 focus:shadow-outline transition ease-in-out duration-150 sm:text-sm sm:leading-5">
					Cancel
				</button>
			</span>
		</div>
	</div>
</div>
{/if}
{/if}
