<script>
	import { goto, stores } from '@sapper/app';
	import { onMount, onDestroy, tick } from 'svelte';
	import { unlockAccount, checkAccount, godModeApproval, mainAPI } from '../../common.js';
	import { account } from '../../stores.js';
	import { uuid } from 'uuidv4';

	const { page } = stores();

	let {slug} = $page.params;

	let jsonStore = null;

	let formFilled = false;
	let showButtonLoader = false;
	let formSubmitted = false;

	let countries = [
		{text: 'India', code: 'IN'},
		{text: 'Canada', code: 'CA'},
		{text: 'United States of America', code: 'US'},
		{text: 'Others', code: 'others'},
	]

	let loading = true;
	let formActionPending = false;
	let formActioned = '';

	let formBody = {
		first_name: '',
		last_name: '',
		email_address: '',
		country: countries[0].code,
		street_address: '',
		city: '',
		state: '',
		postal_code: '',
		movement: '',
		description: '',
		purpose: {
			"emergency": false,
			"essential": false,
			"non-essential": false,
		}
	}

	let status = 'loading..';
	let statusColor = 'gray';

	const formAction = async (action) => {
		formActionPending = true;
		mainAPI.post('/form/'+slug, {action: action}).then((d) => {
			console.log(d.data);
			formActioned = action == 'approve' ? 'approved' : 'rejected';
		}).catch((error) => {
			alert("Something went wrong!");
			formActionPending = false;
			console.error(error);
		});
	}

	const submitForm = async () => {
		console.log(formBody);
		formFilled = false;
		showButtonLoader = true;
		const data = {"ethAddress": $account.ethAddress, formData: JSON.stringify(formBody), uuid: uuid()};
		mainAPI.post('/forms/', data).then((d) => {
			formSubmitted = true;
			console.log(d.data);
		}).catch((error) => {
			formFilled = true;
			showButtonLoader = false;
			alert("Something went wrong!");
			console.error(error);
		});
	}

	$: {
		let formFilledFlag = true;
		for (let i in formBody){
			if (i == 'purpose'){
				if (Object.values(formBody.purpose).indexOf(true) == -1){
					formFilledFlag = false;
					break;
				}
			} else {
				if (formBody[i].trim() == ''){
					formFilledFlag = false;
					break;
				}
			}
		}
		if (formFilledFlag){
			formFilled = true;
		} else {
			formFilled = false;
		}
	}

	onMount(async () => {
		if (!await checkAccount()){
			goto('/');
		}
		jsonStore = localStorage.getItem('jsonStore');
		if (jsonStore){
			//await unlockAccount();
		}
		if (slug == 'new'){
			formBody.email_address = $account.email;
		} else {
			try {
				const response = await mainAPI.get($account.isAdmin ? '/forms/' : '/user/'+$account.ethAddress+'/forms');
				for (let i=0; i<response.data.length; i++){
					const data = response.data[i];
					if (data.uuid == slug){
						formBody = data.formData;
						switch (data.status){
							case -1:
								status = 'pending';
								statusColor = 'gray';
							break;
							case 0:
							case 1:
							case 2:
								status = 'submitted';
								statusColor = 'gray';
							break;
							case 3:
								status = 'approved';
								statusColor = 'green';
							break;
							case 4:
								status = 'rejected';
								statusColor = 'red';
							break;
							default:
								status = data.status;
								statusColor = 'gray';
							break;
						}
						loading = false;
					}
				}
				if (loading){
					alert('Could not load form!');
				}
			}
			catch(e){
				console.error(e);
			}
		}
	});

</script>

{#if $account}
<div class="sm:mx-auto sm:w-full sm:max-w-md">
	<h2 class="mt-6 text-center text-3xl leading-9 font-extrabold text-gray-900">
		{slug == 'new' ? 'New Application' : 'Application '+(loading ? 'loading...' : '- '+slug.substr(0, 8))}
	</h2>
</div>

<div class="mt-6 bg-white shadow px-4 py-5 sm:rounded-lg sm:p-6">
	<div class="md:grid md:grid-cols-3 md:gap-6">
		<div class="md:col-span-1">
			<h3 class="text-lg font-medium leading-6 text-gray-900">Personal Information</h3>
			<p class="mt-1 text-sm leading-5 text-gray-500">
				Use an address which is preferably tied to your ID.
			</p>
		</div>
		<div class="mt-5 md:mt-0 md:col-span-2">
				<div class="grid grid-cols-6 gap-6">
					<div class="col-span-6 sm:col-span-3">
						<label for="first_name" class="block text-sm font-medium leading-5 text-gray-700">First name</label>
						<input id="first_name" bind:value={formBody.first_name} class="mt-1 form-input block w-full py-2 px-3 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:shadow-outline-blue focus:border-blue-300 transition duration-150 ease-in-out sm:text-sm sm:leading-5" />
					</div>

					<div class="col-span-6 sm:col-span-3">
						<label for="last_name" class="block text-sm font-medium leading-5 text-gray-700">Last name</label>
						<input id="last_name" bind:value={formBody.last_name} class="mt-1 form-input block w-full py-2 px-3 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:shadow-outline-blue focus:border-blue-300 transition duration-150 ease-in-out sm:text-sm sm:leading-5" />
					</div>

					<div class="col-span-6 sm:col-span-4">
						<label for="email_address" class="block text-sm font-medium leading-5 text-gray-700">Email address</label>
						<input id="email_address" bind:value={formBody.email_address} class="opacity-50 cursor-not-allowed mt-1 form-input block w-full py-2 px-3 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:shadow-outline-blue focus:border-blue-300 transition duration-150 ease-in-out sm:text-sm sm:leading-5" disabled />
					</div>

					<div class="col-span-6 sm:col-span-3">
						<label for="country" class="block text-sm font-medium leading-5 text-gray-700">Country / Region</label>
						<select id="country" bind:value={formBody.country} class="mt-1 block form-select w-full py-2 px-3 py-0 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:shadow-outline-blue focus:border-blue-300 transition duration-150 ease-in-out sm:text-sm sm:leading-5">
			{#each countries as country}
				<option value={country.code}>
					{country.text}
				</option>
			{/each}
						</select>
					</div>

					<div class="col-span-6">
						<label for="street_address" class="block text-sm font-medium leading-5 text-gray-700">Street address</label>
						<input id="street_address" bind:value={formBody.street_address} class="mt-1 form-input block w-full py-2 px-3 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:shadow-outline-blue focus:border-blue-300 transition duration-150 ease-in-out sm:text-sm sm:leading-5" />
					</div>

					<div class="col-span-6 sm:col-span-6 lg:col-span-2">
						<label for="city" class="block text-sm font-medium leading-5 text-gray-700">City</label>
						<input id="city" bind:value={formBody.city} class="mt-1 form-input block w-full py-2 px-3 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:shadow-outline-blue focus:border-blue-300 transition duration-150 ease-in-out sm:text-sm sm:leading-5" />
					</div>

					<div class="col-span-6 sm:col-span-3 lg:col-span-2">
						<label for="state" class="block text-sm font-medium leading-5 text-gray-700">State / Province</label>
						<input id="state" bind:value={formBody.state} class="mt-1 form-input block w-full py-2 px-3 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:shadow-outline-blue focus:border-blue-300 transition duration-150 ease-in-out sm:text-sm sm:leading-5" />
					</div>

					<div class="col-span-6 sm:col-span-3 lg:col-span-2">
						<label for="postal_code" class="block text-sm font-medium leading-5 text-gray-700">ZIP / Postal</label>
						<input id="postal_code" bind:value={formBody.postal_code} class="mt-1 form-input block w-full py-2 px-3 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:shadow-outline-blue focus:border-blue-300 transition duration-150 ease-in-out sm:text-sm sm:leading-5" />
					</div>
				</div>
		</div>
	</div>
</div>

<div class="mt-6 bg-white shadow px-4 py-5 sm:rounded-lg sm:p-6">
	<div class="md:grid md:grid-cols-3 md:gap-6">
		<div class="md:col-span-1">
			<h3 class="text-lg font-medium leading-6 text-gray-900">Pass Parameters</h3>
			<p class="mt-1 text-sm leading-5 text-gray-500">
				Please only enter as per your requirement to avoid delay in processing.
			</p>
		</div>
		<div class="mt-5 md:mt-0 md:col-span-2">
				<fieldset>
					<legend class="text-base leading-6 font-medium text-gray-900">Purpose</legend>
					<div class="mt-4">
						<div class="flex items-start">
							<div class="absolute flex items-center h-5">
								<input id="comments" bind:checked={formBody.purpose.emergency} type="checkbox" class="form-checkbox h-4 w-4 text-indigo-600 transition duration-150 ease-in-out" />
							</div>
							<div class="pl-7 text-sm leading-5">
								<label for="comments" class="font-medium text-gray-700">Emergency</label>
								<p class="text-gray-500">Health emergencies, helping another person.</p>
							</div>
						</div>
						<div class="mt-4">
							<div class="flex items-start">
								<div class="absolute flex items-center h-5">
									<input id="candidates" bind:checked={formBody.purpose.essential} type="checkbox" class="form-checkbox h-4 w-4 text-indigo-600 transition duration-150 ease-in-out" />
								</div>
								<div class="pl-7 text-sm leading-5">
									<label for="candidates" class="font-medium text-gray-700">Essential</label>
									<p class="text-gray-500">To get groceries, etc.</p>
								</div>
							</div>
						</div>
						<div class="mt-4">
							<div class="flex items-start">
								<div class="absolute flex items-center h-5">
									<input id="offers" bind:checked={formBody.purpose['non-essential']} type="checkbox" class="form-checkbox h-4 w-4 text-indigo-600 transition duration-150 ease-in-out" />
								</div>
								<div class="pl-7 text-sm leading-5">
									<label for="offers" class="font-medium text-gray-700">Non-essential</label>
									<p class="text-gray-500">For general movement (explain).</p>
								</div>
							</div>
						</div>
					</div>
				</fieldset>
				<div class="mt-6">
					<label for="about" class="block text-sm leading-5 font-medium text-gray-700">
						Description
					</label>
					<div class="rounded-md shadow-sm">
						<textarea id="about" rows="3" bind:value={formBody.description} class="form-textarea mt-1 block w-full transition duration-150 ease-in-out sm:text-sm sm:leading-5" placeholder="Brief description of why you want a pass"></textarea>
					</div>
				</div>
				<fieldset class="mt-6">
					<legend class="text-base leading-6 font-medium text-gray-900">Movement</legend>
					<p class="text-sm leading-5 text-gray-500">Which geographies do you need to move between?</p>
					<div class="mt-4">
						<div class="flex items-center">
							<input id="movement_city" bind:group={formBody.movement} value="city" name="form-input movement" type="radio" class="form-radio h-4 w-4 text-indigo-600 transition duration-150 ease-in-out" />
							<label for="push_everything" class="ml-3">
								<span class="block text-sm leading-5 font-medium text-gray-700">Within City</span>
							</label>
						</div>
						<div class="mt-4 flex items-center">
							<input id="movement_state" bind:group={formBody.movement} value="state" name="form-input movement" type="radio" class="form-radio h-4 w-4 text-indigo-600 transition duration-150 ease-in-out" />
							<label for="push_email" class="ml-3">
								<span class="block text-sm leading-5 font-medium text-gray-700">Within State</span>
							</label>
						</div>
						<div class="mt-4 flex items-center">
							<input id="movement_country" bind:group={formBody.movement} value="country" name="form-input movement" type="radio" class="form-radio h-4 w-4 text-indigo-600 transition duration-150 ease-in-out" />
							<label for="push_nothing" class="ml-3">
								<span class="block text-sm leading-5 font-medium text-gray-700">Inter-state</span>
							</label>
						</div>
					</div>
				</fieldset>
		</div>
	</div>
</div>
{#if !formFilled}
<div class="mt-4 pt-3">
	<div class="rounded-md bg-red-50 p-4">
		<div class="flex">
			<div class="flex-shrink-0">
				<svg class="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
					<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
				</svg>
			</div>
			<div class="ml-3">
				<h3 class="text-sm leading-5 font-medium text-red-800">
					All fields are required!
				</h3>
			</div>
		</div>
	</div>
</div>
{/if}
<div class="mt-8 border-t border-gray-200 pt-5">
	<div class="flex justify-end">
		{#if slug == 'new'}
			{#if formFilled}
			<span class="ml-3 inline-flex rounded-md shadow-sm">
				<button type="submit" on:click={submitForm} class="w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-500 focus:outline-none focus:border-indigo-700 focus:shadow-outline-indigo active:bg-indigo-700 transition duration-150 ease-in-out">
				Submit Application
				</button>
			</span>
			{:else}
			<span class="inline-flex rounded-md shadow-sm">
				<button type="button" on:click={() => {goto('/forms')}} class="py-2 px-4 border border-gray-300 rounded-md text-sm leading-5 font-medium text-gray-700 hover:text-gray-500 focus:outline-none focus:border-blue-300 focus:shadow-outline-blue active:bg-gray-50 active:text-gray-800 transition duration-150 ease-in-out">
					Cancel
				</button>
			</span>
			<span class="ml-3 inline-flex rounded-md shadow-sm">
				<button type="submit" class="opacity-50 cursor-not-allowed w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-500 focus:outline-none focus:border-indigo-700 focus:shadow-outline-indigo active:bg-indigo-700 transition duration-150 ease-in-out">
					{#if showButtonLoader}
					Submitting Application <div class="lds-ring"><div></div><div></div><div></div><div></div></div>
					{:else}
					Submit Application
					{/if}
				</button>
			</span>
			{/if}
		{:else}
			{#if (godModeApproval || $account.isAdmin) && status == 'submitted' && !loading}
			<span class="inline-flex rounded-md shadow-sm {formActionPending ? 'opacity-50 cursor-not-allowed' : ''}">
				<button type="submit" on:click={ () => formAction('approve')} class="w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-500 focus:outline-none focus:border-indigo-700 focus:shadow-outline-indigo active:bg-indigo-700 transition duration-150 ease-in-out">
				{godModeApproval && !$account.isAdmin ? 'Self ' : ''}Approve Application
				</button>
			</span>
			<span class="ml-3 inline-flex rounded-md shadow-sm {formActionPending ? 'opacity-50 cursor-not-allowed' : ''}">
				<button type="submit" on:click={ () => formAction('reject')} class="w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-red-700 bg-red-100 hover:bg-red-50 focus:outline-none focus:border-red-700 focus:shadow-outline-red active:bg-red-700 transition duration-150 ease-in-out">
				Reject
				</button>
			</span>
			{:else}
			<div class="ml-2 flex-shrink-0 flex">
				<span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-{statusColor}-100 text-{statusColor}-800">
					{status}
				</span>
			</div>
			{/if}
		{/if}
	</div>
</div>
{/if}
{#if formSubmitted}
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
				<h3 class="text-lg leading-6 font-medium text-gray-900">
					Submission successful
				</h3>
				<div class="mt-2">
					<p class="text-sm leading-5 text-gray-500">
						Your form has been submitted. Once approved/rejected, we will notify you.
					</p>
				</div>
			</div>
		</div>
		<div class="mt-5 sm:mt-6">
			<span class="flex w-full rounded-md shadow-sm">
				<button type="button" on:click={() => {goto('/forms')}} class="inline-flex justify-center w-full rounded-md border border-transparent px-4 py-2 bg-indigo-600 text-base leading-6 font-medium text-white shadow-sm hover:bg-indigo-500 focus:outline-none focus:border-indigo-700 focus:shadow-outline-indigo transition ease-in-out duration-150 sm:text-sm sm:leading-5">
					Check Status
				</button>
			</span>
		</div>
	</div>
</div>
{/if}

{#if formActioned}
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
				<h3 class="text-lg leading-6 font-medium text-gray-900">
					Action successful
				</h3>
				<div class="mt-2">
					<p class="text-sm leading-5 text-gray-500">
						The form has been {formActioned}.
					</p>
				</div>
			</div>
		</div>
		<div class="mt-5 sm:mt-6">
			<span class="flex w-full rounded-md shadow-sm">
				<button type="button" on:click={() => {goto('/forms')}} class="inline-flex justify-center w-full rounded-md border border-transparent px-4 py-2 bg-indigo-600 text-base leading-6 font-medium text-white shadow-sm hover:bg-indigo-500 focus:outline-none focus:border-indigo-700 focus:shadow-outline-indigo transition ease-in-out duration-150 sm:text-sm sm:leading-5">
					Go back to Forms
				</button>
			</span>
		</div>
	</div>
</div>
{/if}
