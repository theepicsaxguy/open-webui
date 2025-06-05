import { WEBUI_API_BASE_URL } from '$lib/constants';

export const ingestGitRepo = async (
    token: string,
    payload: {
        source: string;
        branch?: string | null;
        commit?: string | null;
        subpath?: string | null;
        max_depth?: number | null;
        ingest_file_content?: boolean | null;
    }
) => {
    let error = null;

    const res = await fetch(`${WEBUI_API_BASE_URL}/git-ingest/ingest`, {
        method: 'POST',
        headers: {
            Accept: 'application/json',
            'Content-Type': 'application/json',
            authorization: `Bearer ${token}`
        },
        body: JSON.stringify(payload)
    })
        .then(async (res) => {
            if (!res.ok) throw await res.json();
            return res.json();
        })
        .catch((err) => {
            error = err.detail || err;
            console.error(err);
            return null;
        });

    if (error) {
        throw error;
    }

    return res;
};
