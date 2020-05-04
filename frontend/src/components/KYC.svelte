<script>
	import { mainAPI } from '../common.js';
	import { account } from '../stores.js';

	let kycId= '';
	let showKyc = false;
	export let showStatus = true;
	export let buttonText = 'Start KYC';

	const requestKYC = async (type) => {
		console.log('requesting KYC');
		kycId = 'generating';
		mainAPI.post('/user/'+$account.ethAddress, {action: (type == 'mock' ? "initiateMockVerify" : "initiateVerify"), return_url: location.origin}).then((d) => {
			console.log(d.data);
			if (!d.data.redirect){
				kycId = 'pending';
				showKyc = false;
				alert("KYC already pending!");
			} else {
				//kycId = d.data.redirect;
				window.location = d.data.redirect;
			}
			let account_data = $account;
			account_data.kycVerified = 'pending';
			account.set(account_data);
		}).catch((error) => {
			alert("Something went wrong!");
			kycId = '';
			showKyc = false;
			console.error(error);
		});
	}
	console.log('showStatus', showStatus, typeof(showStatus));

</script>

{#if $account.kycVerified == 'verified'}
	{showStatus === true ? 'Verified' : ''}
{:else if $account.kycVerified =='pending' || $account.kycVerified =='requested' || kycId == 'pending'}
	{showStatus === true ? 'Processing' : ''}
{:else if kycId == ''}
	{#if $account.kycVerified == 'failed'}
		{showStatus === true ? 'Failed' : ''}
	{:else}
		{showStatus === true ? 'Incomplete' : ''}
	{/if}
	<button type="button" on:click={() => {showKyc = true;}} class="inline-flex items-center px-4 py-2 border border-transparent text-sm leading-5 font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-500 focus:outline-none focus:border-indigo-700 focus:shadow-outline-indigo active:bg-indigo-700 transition ease-in-out duration-150">
		{buttonText}
	</button>
{:else if kycId == 'generating'}
	<button type="button" class="opacity-50 cursor-not-allowed inline-flex items-center px-4 py-2 border border-transparent text-sm leading-5 font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-500 focus:outline-none focus:border-indigo-700 focus:shadow-outline-indigo active:bg-indigo-700 transition ease-in-out duration-150">
		Generating Request <div class="lds-ring"><div></div><div></div><div></div><div></div></div>
	</button>
{:else}
	Pending - <a href={kycId} target="_blank">open link</a>
{/if}

{#if showKyc}
<div x-show="open" class="fixed bottom-0 inset-x-0 px-4 pb-6 sm:inset-0 sm:p-0 sm:flex sm:items-center sm:justify-center">
	<div x-show="open" x-transition:enter="ease-out duration-300" x-transition:enter-start="opacity-0" x-transition:enter-end="opacity-100" x-transition:leave="ease-in duration-200" x-transition:leave-start="opacity-100" x-transition:leave-end="opacity-0" class="fixed inset-0 transition-opacity">
		<div class="absolute inset-0 bg-gray-500 opacity-75"></div>
	</div>

	<div x-show="open" x-transition:enter="ease-out duration-300" x-transition:enter-start="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95" x-transition:enter-end="opacity-100 translate-y-0 sm:scale-100" x-transition:leave="ease-in duration-200" x-transition:leave-start="opacity-100 translate-y-0 sm:scale-100" x-transition:leave-end="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95" class="bg-white rounded-lg px-4 pt-5 pb-4 overflow-hidden shadow-xl transform transition-all sm:max-w-sm sm:w-full sm:p-6">
		<div>
			<div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
				<svg fill="currentColor" viewBox="0 0 20 20" class="w-8 h-8"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-6-3a2 2 0 11-4 0 2 2 0 014 0zm-2 4a5 5 0 00-4.546 2.916A5.986 5.986 0 0010 16a5.986 5.986 0 004.546-2.084A5 5 0 0010 11z" clip-rule="evenodd"></path></svg>
			</div>
			<div class="mt-3 text-center sm:mt-5">
				<h3 class="text-lg leading-6 font-medium text-gray-900">
					KYC Request
				</h3>
				<div class="mt-2">
					<p class="text-sm leading-5 text-gray-500">
						We need to authenticate you via an ID and a selfie to prove your identity. Alternatively, you can simulate the process by chosing the mock option and we will prefill the pass using dummy data.
					</p>
				</div>
			</div>
		</div>
		{#if kycId == 'generating'}
		<div class="mt-5 sm:mt-6">
			<span class="flex w-full rounded-md shadow-sm">
				<button type="button" class="opacity-50 cursor-not-allowed inline-flex justify-center w-full rounded-md border border-transparent px-4 py-2 bg-indigo-600 text-base leading-6 font-medium text-white shadow-sm hover:bg-indigo-500 focus:outline-none focus:border-indigo-700 focus:shadow-outline-indigo transition ease-in-out duration-150 sm:text-sm sm:leading-5">
					Requesting KYC <div class="lds-ring"><div></div><div></div><div></div><div></div></div>
				</button>
			</span>
		</div>
		{:else}
		<div class="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
			<span class="flex w-full rounded-md shadow-sm sm:col-start-1">
				<button type="button" on:click={() => {
						requestKYC('mock');
						//window.location = kycId;
					}} class="inline-flex justify-center w-full rounded-md border border-gray-300 px-4 py-2 bg-white text-base leading-6 font-medium text-gray-700 shadow-sm hover:text-gray-500 focus:outline-none focus:border-blue-300 focus:shadow-outline transition ease-in-out duration-150 sm:text-sm sm:leading-5">
					Mock KYC
				</button>
			</span>
			<span class="mt-3 flex w-full rounded-md shadow-sm sm:mt-0 sm:col-start-2">
				<button type="button" on:click={requestKYC} class="inline-flex justify-center w-full rounded-md border border-transparent px-4 py-2 bg-indigo-600 text-base leading-6 font-medium text-white shadow-sm hover:bg-indigo-500 focus:outline-none focus:border-indigo-700 focus:shadow-outline-indigo transition ease-in-out duration-150 sm:text-sm sm:leading-5">
					Use Real KYC
				</button>
			</span>
		</div>
		{/if}
	</div>
</div>
{/if}
