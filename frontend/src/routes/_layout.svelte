<script>
	import Tailwindcss from '../components/Tailwindcss.svelte';
	import Nav from '../components/Nav.svelte';
	import { goto } from '@sapper/app';
	import { account } from '../stores.js';
	import { SENTRY, GOOGLE_ANALYTICS, FULLSTORY } from '../common.js';

	export let segment;

	let opened = false;
	const openedTabClass = "ml-4 px-3 py-2 rounded-md text-sm font-medium text-white bg-gray-900 focus:outline-none focus:text-white focus:bg-gray-700";
	const unopenedTabClass = "ml-4 px-3 py-2 rounded-md text-sm font-medium text-gray-300 hover:text-white hover:bg-gray-700 focus:outline-none focus:text-white focus:bg-gray-700";
	const openedMobileTabClass = "block px-3 py-2 rounded-md text-base font-medium text-white bg-gray-900 focus:outline-none focus:text-white focus:bg-gray-700";
	const unopenedMobileTabClass = "mt-1 block px-3 py-2 rounded-md text-base font-medium text-gray-300 hover:text-white hover:bg-gray-700 focus:outline-none focus:text-white focus:bg-gray-700";

	let mobileOpened = false;

	const logout = async () => {
		alert('disabled logout');
		opened = false;
		return;
		/*
		account.set('');
		localStorage.removeItem('adabdha_user');
		goto('/');
		*/
	}

	let notification = false;

	const clearNotification = () => {
		notification = false;
	}

</script>

<svelte:head>

{@html SENTRY}

{@html GOOGLE_ANALYTICS}

{@html FULLSTORY}

</svelte:head>

<Tailwindcss />

<div class="flex flex-col h-screen justify-between">
	<nav class="bg-gray-800">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
			<div class="flex items-center justify-between h-16">
				<div class="flex items-center">
					<div class="flex-shrink-0">
						<a class="cursor-pointer" href="/">
							<img class="h-8 w-8" src="/adabdha_logo_square.png" alt="Adabdha logo" />
						</a>
					</div>
					{#if $account}
					<div class="hidden md:block">
						<div class="ml-10 flex items-baseline">
							<a href="/" on:click={() => goto('/forms')} class={segment == undefined || segment == '' ? openedTabClass : unopenedTabClass}>Dashboard</a>
							<a href="/passes" on:click={() => goto('/forms')} class={segment == 'passes' ? openedTabClass : unopenedTabClass}>Passes</a>
							<a href="/forms" on:click={() => goto('/forms')} class={segment == 'forms' ? openedTabClass : unopenedTabClass}>Forms</a>
						</div>
					</div>
					{/if}
				</div>
				<div class="hidden md:block">
					<div class="ml-4 flex items-center md:ml-6">
					{#if $account && $account.isAdmin}
						<div class="ml-3 relative">
							<div>
								<button class="max-w-xs flex items-center text-sm rounded-full text-white focus:outline-none focus:shadow-solid" id="user-menu" aria-label="User menu" aria-haspopup="true" x-bind:aria-expanded="open" on:click={() => {
										opened = opened ? false : true;
									}}>
									<img class="h-8 w-8 rounded-full" src="https://images.unsplash.com/photo-1513144645912-f06fb3fcd35e?ixlib=rb-1.2.1&q=80&fm=jpg&crop=entropy&cs=tinysrgb&dl=joseph-chan-pJjUgPm_VTA-unsplash.jpg&w=640" alt="Harambe" />
									{#if $account.isAdmin}
									<span class="absolute top-0 right-0 block h-1.5 w-1.5 rounded-full text-white shadow-solid bg-green-300"></span>
									{:else}
									<span class="absolute top-0 right-0 block h-1.5 w-1.5 rounded-full text-white shadow-solid bg-gray-300"></span>
									{/if}
								</button>
							</div>
						{#if opened}
							<div x-show="close" x-transition:enter="transition ease-out duration-100" x-transition:enter-start="transform opacity-0 scale-95" x-transition:enter-end="transform opacity-100 scale-100" x-transition:leave="transition ease-in duration-75" x-transition:leave-start="transform opacity-100 scale-100" x-transition:leave-end="transform opacity-0 scale-95" class="origin-top-right absolute right-0 mt-2 w-48 rounded-md shadow-lg">
								<div class="py-1 rounded-md bg-white shadow-xs">
									{#if $account.isAdmin}
									<a href="#godMode" on:click={() => {
										let account_data = $account;
										account_data.godMode = account_data.godMode ? false : true;
										account.set(account_data);
										//notification = true;
										//setTimeout(clearNotification, 5000);
										opened = false;
									}} class="cursor-pointer block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">{$account.godMode ? 'Leave' : 'Switch to'} God Mode</a>
									{/if}
									<a href="#logout" on:click={logout} class="cursor-pointer block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">Sign out</a>
								</div>
							</div>
						{/if}
						</div>
					{/if}
					</div>
				</div>
				{#if $account}
				<div class="-mr-2 flex md:hidden">
					<button	on:click={() => {mobileOpened = mobileOpened ? false : true; }} class="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-white hover:bg-gray-700 focus:outline-none focus:bg-gray-700 focus:text-white" x-bind:aria-label="open ? 'Close main menu' : 'Main menu'" x-bind:aria-expanded="open">
						<svg class="h-6 w-6" stroke="currentColor" fill="none" viewBox="0 0 24 24">
							<path class="inline-flex" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
							<path class="hidden" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
						</svg>
					</button>
				</div>
				{/if}
			</div>
		</div>
		{#if $account && mobileOpened}
			<div x-description="Mobile menu, toggle classes based on menu state." x-state:on="Open" x-state:off="closed" class="block">
				<div class="px-2 pt-2 pb-3 sm:px-3">
					<a href="/" on:click={() => {mobileOpened=false; goto('/')}} class={segment == undefined || segment == '' ? openedMobileTabClass : unopenedMobileTabClass}>Dashboard</a>
					<a href="/passes" on:click={() => {mobileOpened=false; goto('/passes')}} class={segment == 'passes' ? openedMobileTabClass : unopenedMobileTabClass}>Passes</a>
					<a href="/forms" on:click={() => {mobileOpened=false; goto('/forms')}} class={segment == 'forms' ? openedMobileTabClass : unopenedMobileTabClass}>Forms</a>
				</div>
				{#if $account && $account.isAdmin}
					<div class="pt-4 pb-3 border-t border-gray-700">
						<div class="flex items-center px-5">
							<div class="flex-shrink-0">
								<img class="h-10 w-10 rounded-full" src="https://images.unsplash.com/photo-1513144645912-f06fb3fcd35e?ixlib=rb-1.2.1&q=80&fm=jpg&crop=entropy&cs=tinysrgb&dl=joseph-chan-pJjUgPm_VTA-unsplash.jpg&w=640" alt="Harambe" />
							</div>
						</div>
						<div class="mt-3 px-2">
							{#if $account.isAdmin}
							<a href="#godMode" on:click={() => {
								let account_data = $account;
								account_data.godMode = account_data.godMode ? false : true;
								account.set(account_data);
								//notification = true;
								//setTimeout(clearNotification, 5000);
								mobileOpened = false;
							}} class="block px-3 py-2 rounded-md text-base font-medium text-gray-400 hover:text-white hover:bg gray-700 focus:outline-none focus:text-white focus:bg-gray-700">
							{$account.godMode ? 'Leave' : 'Switch to'} God Mode</a>
							{/if}
							<a href="#logout" on:click={logout} class="mt-1 block px-3 py-2 rounded-md text-base font-medium text-gray-400 hover:text-white hover:bg-gray-700 focus:outline-none focus:text-white focus:bg-gray-700">Sign out</a>
						</div>
					</div>
				{/if}
			</div>
		{/if}
	</nav>
	<header class="bg-white shadow-sm">
		<div class="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
			<h1 class="text-lg leading-6 font-semibold text-gray-900 capitalize" >
				{segment || 'Dashboard'}
			</h1>
		</div>
		{#if $account.godMode}
		<div class="rounded-md bg-blue-50 p-4">
			<div class="flex">
				<div class="flex-shrink-0">
					<svg class="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
						<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
					</svg>
				</div>
				<div class="ml-3 flex-1 md:flex md:justify-between">
					<p class="text-sm leading-5 text-blue-700">
						You are on god mode. With great power, comes great responsibilities!
					</p>
					<p class="mt-3 text-sm leading-5 md:mt-0 md:ml-6">
						<button type="button" on:click={() => {
							let account_data = $account;
							account_data.godMode = false;
							account.set(account_data);
							//notification = true;
							//setTimeout(clearNotification, 5000);
						}} class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm leading-5 font-medium rounded-md text-gray-700 bg-white hover:text-gray-500 focus:outline-none focus:border-blue-300 focus:shadow-outline-blue active:text-gray-800 active:bg-gray-50 transition ease-in-out duration-150">
							Leave
						</button>
					</p>
				</div>
			</div>
		</div>
		{/if}
	</header>
	<main class="mb-auto">
		<div class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
			<slot></slot>
		</div>
	</main>
	<footer class="h-10 mb-auto">
		<div class="bg-gray-800">
			<div class="max-w-screen-xl mx-auto py-10 px-4 overflow-hidden sm:px-6 lg:px-8">
				<nav class="-mx-5 -my-2 flex flex-wrap justify-center">
					<div class="px-5 py-2">
						<a href="/terms" class="text-base leading-6 text-gray-500 hover:text-gray-900">
							Terms
						</a>
					</div>
					<div class="px-5 py-2">
						<a href="/privacy" class="text-base leading-6 text-gray-500 hover:text-gray-900">
							Privacy
						</a>
					</div>
					<div class="px-5 py-2">
						<a href="https://blockvigil.com" target="_blank" class="text-base leading-6 text-gray-500 hover:text-gray-900">
							BlockVigil
						</a>
					</div>
				</nav>
				<div class="mt-8 flex justify-center">
				<a href="https://twitter.com/Adabdha" target="_blank" class="text-gray-400 hover:text-gray-500">
					<span class="sr-only">Twitter</span>
					<svg class="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
						<path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.713v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84" />
					</svg>
				</a>
				<a href="https://github.com/blockvigil/adabdha" target="_blank" class="ml-6 text-gray-400 hover:text-gray-500">
					<span class="sr-only">GitHub</span>
					<svg class="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
						<path fill-rule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clip-rule="evenodd" />
					</svg>
				</a>
				<a href="mailto:hello@adabdha.com" target="_blank" class="ml-6 text-gray-400 hover:text-gray-500">
						<span class="sr-only">Email</span>
						<svg class="flex-shrink-0 h-6 w-6 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
						</svg>
					</a>
				<a href="https://www.facebook.com/Adabdha" target="_blank" class="ml-6 text-gray-400 hover:text-gray-500">
					<span class="sr-only">Facebook</span>
					<svg class="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
						<path fill-rule="evenodd" d="M22 12c0-5.523-4.477-10-10-10S2 6.477 2 12c0 4.991 3.657 9.128 8.438 9.878v-6.987h-2.54V12h2.54V9.797c0-2.506 1.492-3.89 3.777-3.89 1.094 0 2.238.195 2.238.195v2.46h-1.26c-1.243 0-1.63.771-1.63 1.562V12h2.773l-.443 2.89h-2.33v6.988C18.343 21.128 22 16.991 22 12z" clip-rule="evenodd" />
					</svg>
				</a>
				</div>
				<div class="mt-8">
					<p class="text-center text-base leading-6 text-gray-400">
						&#xA9; 2020 BlockVigil, Inc. All rights reserved.
					</p>
				</div>
			</div>
		</div>
	</footer>
</div>
