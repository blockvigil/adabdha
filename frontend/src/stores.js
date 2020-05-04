import { writable } from 'svelte/store';

export const progressvar = writable(false);

export const account = writable('');
export const wsTxStore = writable('');
