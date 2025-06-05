<script lang="ts">
    import { onMount, getContext } from 'svelte';
    import { ingestGitRepo } from '$lib/apis/git_ingest';
    import { user } from '$lib/stores';
    const i18n = getContext('i18n');

    let source = '';
    let branch: string | null = null;
    let commit: string | null = null;
    let subpath: string | null = null;
    let maxDepth: number = 20;
    let ingestContent = true;

    let loading = false;
    let result: any = null;
    let error: any = null;

    const submit = async () => {
        loading = true;
        error = null;
        result = null;
        try {
            result = await ingestGitRepo(localStorage.token, {
                source,
                branch,
                commit,
                subpath,
                max_depth: maxDepth,
                ingest_file_content: ingestContent
            });
        } catch (err) {
            error = err;
        } finally {
            loading = false;
        }
    };
</script>

<div class="flex flex-col gap-4 p-4 max-w-3xl mx-auto">
    <h2 class="text-xl font-semibold">Git Ingest Demo</h2>
    <div class="flex flex-col gap-2">
        <input class="input" placeholder="Repository URL or Path" bind:value={source} />
        <div class="flex gap-2">
            <input class="input flex-1" placeholder="Branch" bind:value={branch} />
            <input class="input flex-1" placeholder="Commit" bind:value={commit} />
        </div>
        <input class="input" placeholder="Subpath" bind:value={subpath} />
        <div class="flex gap-2 items-center">
            <label class="text-sm">Max Depth</label>
            <input type="number" class="input w-20" bind:value={maxDepth} min="1" />
            <label class="ml-4 flex items-center gap-1 text-sm">
                <input type="checkbox" bind:checked={ingestContent} />
                Ingest File Content
            </label>
        </div>
        <button class="btn" on:click={submit} disabled={loading}>
            {loading ? 'Ingesting...' : 'Ingest'}
        </button>
    </div>

    {#if error}
        <div class="text-red-600">{error}</div>
    {/if}

    {#if result}
        <h3 class="font-semibold mt-4">{result.Summary}</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
            <pre class="p-2 bg-gray-50 dark:bg-gray-900 rounded overflow-auto">
{result.DirectoryTree}
            </pre>
            <pre class="p-2 bg-gray-50 dark:bg-gray-900 rounded overflow-auto max-h-96">
{result.FileContent}
            </pre>
        </div>
    {/if}
</div>

<style>
    .input {
        @apply w-full rounded-md p-2 border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm;
    }
    .btn {
        @apply bg-blue-600 hover:bg-blue-700 text-white font-medium px-4 py-2 rounded;
    }
</style>
