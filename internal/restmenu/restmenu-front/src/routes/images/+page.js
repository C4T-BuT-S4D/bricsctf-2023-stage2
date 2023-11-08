import {PUBLIC_BASE_URL} from "$env/static/public";

/** @type {import('./$types').PageLoad} */
export async function load({fetch}) {
    const res = await fetch(`${PUBLIC_BASE_URL}/api/file`, {
        credentials: 'include'
    });
    if (res.ok) {
        let files = await res.json();
        return {files: files.files};
    }
    return {files: []};
}