<script>
	import { goto } from '@sapper/app';
	import { onMount, onDestroy, tick } from 'svelte';
	import { unlockAccount, checkAccount, godModeApproval, mainAPI } from '../../common.js';
	import { account, wsTxStore } from '../../stores.js';
	import { fly } from 'svelte/transition';

	let formHashes = [];
	let forms = [];
	let loading = true;
	let uuids = [];
	let notification = {};

	const unsubscribeWTX = wsTxStore.subscribe(value => {
		if (value){
			console.log('got ws', value);
			if (value.data.uuidHash){
				const pos = formHashes.indexOf(value.data.uuidHash);
				if (pos != -1){
					console.log('found uuid, refreshing forms', forms[pos]);
					switch (value.name){
						case 'NewForm':
							forms[pos].status = 'submitted';
							forms[pos].statusColor = 'gray';
						break;
						case 'FormApproved':
							forms[pos].status = 'approved';
							forms[pos].statusColor = 'green';
						break;
						case 'FormRejected':
							forms[pos].status = 'rejected';
							forms[pos].statusColor = 'red';
						break;
						forms = forms;
					}
					notification = {
						uuid: forms[pos].uuid.substr(0, 8),
						status: forms[pos].status
					}
					setTimeout(clearNotification, 5000);
				}
			}
		}
	});

	let account_data = {};

	const unsubscribeAccount = account.subscribe(value => {
		if (value && value.godMode != account_data.godMode && !loading){
			account_data = value;
			loading = true;
			getForms();
		}
	});

	const clearNotification = () => {
		notification = {};
	}

	onMount(async () => {
		if (await checkAccount()){
			getForms();
		} else {
			goto('/');
		}
	});

	onDestroy(async () => {
		unsubscribeWTX();
		unsubscribeAccount();
	});

	const getForms = async () => {
		forms = [];
		uuids = [];
		formHashes = [];
		try {
			const response = await mainAPI.get($account.godMode ? '/forms/' : '/user/'+$account.ethAddress+'/forms');
			for (let i=0; i<response.data.length; i++){
				const data = response.data[i];
				if (uuids.indexOf(data.uuid) != -1){
					console.warn('duplicate', data.uuid);
					continue;
				}
				uuids.push(data.uuid);
				data.formData.purposeString = "";
				switch (data.status){
					case -1:
						data.status = 'pending';
						data.statusColor = 'gray';
					break;
					case 0:
					case 1:
					case 2:
						data.status = 'submitted';
						data.statusColor = 'gray';
					break;
					case 3:
						data.status = 'approved';
						data.statusColor = 'green';
					break;
					case 4:
						data.status = 'rejected';
						data.statusColor = 'red';
					break;
				}
				for (let j in data.formData.purpose){
					if (data.formData.purpose[j]){
						if (data.formData.purposeString){
							data.formData.purposeString += ', '+j;
						} else {
							data.formData.purposeString = j;
						}
					}
				}
				formHashes.push(data.uuidHash);
				forms = [...forms, data];
			}
			loading = false;
		}
		catch(e){
			console.error(e);
		}
	}
</script>

{#if !$account.godMode}
{#if godModeApproval}
<div class="rounded-md bg-blue-50 p-4">
	<div class="flex">
		<div class="flex-shrink-0">
			<svg class="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
				<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
			</svg>
		</div>
		<div class="ml-3 flex-1 md:flex md:justify-between">
			<p class="text-sm leading-5 text-blue-700">
				In this demo mode, you are allowed to self-approve forms. Ideally, only authorized authorities would be allowed to do so.
			</p>
		</div>
	</div>
	<div> </div>
</div>
{/if}
<div class="mt-3 sm:mt-2">
	<div class="max-w-3xl mx-auto space-y-4 flex flex-col items-center justify-start sm:space-y-0 sm:flex-row sm:items-end sm:justify-around">
		<span class="inline-flex rounded-md shadow-sm">
			<button type="button" on:click={() => {goto('/forms/new')}} class="inline-flex items-center px-4 py-2 border border-transparent text-sm leading-5 font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-500 focus:outline-none focus:border-indigo-700 focus:shadow-outline-indigo active:bg-indigo-700 transition ease-in-out duration-150">
				New Form
			</button>
		</span>
	</div>
</div>
{/if}
<div class="mt-6 sm:mt-5">
<div class="bg-white shadow overflow-hidden sm:rounded-md">
	{loading ? 'Loading forms...' : ''}
	<ul>
	{#each forms as form}
		<li>
			<a href="/forms/{form.uuid}" class="block hover:bg-gray-50 focus:outline-none focus:bg-gray-50 transition duration-150 ease-in-out">
			<div class="px-4 py-4 sm:px-6">
				<div class="flex items-center justify-between">
					<div class="text-sm leading-5 font-medium text-indigo-600 truncate">
						{form.uuid.substr(0, 8)} - {form.formData.first_name} {form.formData.last_name}
					</div>
					<div class="ml-2 flex-shrink-0 flex">
						<span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-{form.statusColor}-100 text-{form.statusColor}-800">
							{form.status}
						</span>
					</div>
				</div>
				<div class="mt-2 sm:flex sm:justify-between">
					<div class="sm:flex">
						<div class="mr-6 flex items-center text-sm leading-5 text-gray-500 capitalize">
						<svg class="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
							<path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z"/>
						</svg>
						{form.formData.purposeString}
						</div>
						<div class="mt-2 flex items-center text-sm leading-5 text-gray-500 sm:mt-0 capitalize">
						<svg class="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
							<path fill-rule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd"/>
						</svg>
						Within {form.formData.movement}
						</div>
					</div>
					<div class="mt-2 flex items-center text-sm leading-5 text-gray-500 sm:mt-0">
						<svg class="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
						<path fill-rule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clip-rule="evenodd"/>
						</svg>
						<span>
						<time datetime={new Date(form.timestamp*1000)}>{new Date(form.timestamp*1000)}</time>
						</span>
					</div>
				</div>
			</div>
			</a>
		</li>
	{/each}
</ul>
</div>
</div>
{#if notification.uuid}
<div class="fixed inset-0 flex items-end justify-center px-4 py-6 pointer-events-none sm:p-6 sm:items-start sm:justify-end">
  <!--
    Notification panel, show/hide based on alert state.

    Entering: "transform ease-out duration-300 transition"
      From: "translate-y-2 opacity-0 sm:translate-y-0 sm:translate-x-2"
      To: "translate-y-0 opacity-100 sm:translate-x-0"
    Leaving: "transition ease-in duration-100"
      From: "opacity-100"
      To: "opacity-0"
  -->
  <div class="max-w-sm w-full bg-white shadow-lg rounded-lg pointer-events-auto">
    <div class="rounded-lg shadow-xs overflow-hidden">
      <div class="p-4">
        <div class="flex items-start">
          <div class="flex-shrink-0">
			{#if notification.status == 'rejected'}
			<svg class="h-6 w-6"  viewBox="0 0 20 20" fill="red">
				<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM7 9a1 1 0 000 2h6a1 1 0 100-2H7z" clip-rule="evenodd"></path>
			</svg>
		 	{:else}
            <svg class="h-6 w-6 text-{notification.status == 'rejected' ? 'red' : 'green'}-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
			{/if}
          </div>
          <div class="ml-3 w-0 flex-1 pt-0.5">
            <p class="text-sm leading-5 font-medium text-gray-900">
              Application {notification.uuid} {notification.status}!
            </p>
          </div>
          <div class="ml-4 flex-shrink-0 flex">
            <button on:click={clearNotification} class="inline-flex text-gray-400 focus:outline-none focus:text-gray-500 transition ease-in-out duration-150">
				<svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
					<path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
				</svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
{/if}
