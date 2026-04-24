import { appAvailability } from '$lib/stores/app-availability.svelte';
import { auth } from '$lib/stores/auth.svelte';
import { taxonomy } from '$lib/stores/taxonomy.svelte';
import { toast } from '$lib/stores/toast.svelte';

// Force eager client-side initialization of store modules before route
// components evaluate, avoiding import-order edge cases during reactive setup.
void appAvailability;
void auth;
void taxonomy;
void toast;
