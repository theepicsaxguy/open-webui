<script lang="ts">
import { createEventDispatcher, getContext } from 'svelte';
import Modal from '$lib/components/common/Modal.svelte';
const i18n = getContext('i18n');
const dispatch = createEventDispatcher();

export let show = false;
let source = '';
let branch: string | null = null;
let commit: string | null = null;
let subpath: string | null = null;

const submit = () => {
  if (!source.trim()) return;
  dispatch('submit', { source, branch, commit, subpath });
  show = false;
  source = '';
  branch = null;
  commit = null;
  subpath = null;
};
</script>

<Modal
  size="md"
  containerClassName=""
  className="bg-white dark:bg-gray-900"
  bind:show
>
  <form
    class="flex flex-col gap-2 p-4"
    on:submit|preventDefault={submit}
  >
    <h3 class="text-lg font-medium">
      {$i18n.t('Ingest Git repository')}
    </h3>
    <input
      class="w-full rounded-md p-2 border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
      placeholder={$i18n.t('Repository URL or Path')}
      bind:value={source}
      required
    />
    <div class="flex gap-2">
      <input
        class="input flex-1 rounded-md p-2 border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
        placeholder={$i18n.t('Branch')}
        bind:value={branch}
      />
      <input 
        class="input flex-1 rounded-md p-2 border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
        placeholder={$i18n.t('Commit')}
        bind:value={commit}
      />
    </div>
    <input
      class="w-full rounded-md p-2 border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
      placeholder={$i18n.t('Subpath')}
      bind:value={subpath}
    />
    <div class="flex justify-end gap-2 mt-2">
      <button
        type="button"
        class="px-3 py-1 rounded border border-gray-300 dark:border-gray-700"
        on:click={() => (show = false)}
      >
        {$i18n.t('Cancel')}
      </button>
      <button
        type="submit"
        class="bg-blue-600 hover:bg-blue-700 text-white font-medium px-3 py-1 rounded"
      >
        {$i18n.t('Ingest')}
      </button>
    </div>
  </form>
</Modal>