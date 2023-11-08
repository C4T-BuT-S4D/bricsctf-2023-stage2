import {page} from '$app/stores';
import {PUBLIC_BASE_URL} from "$env/static/public";

/** @type {import('./$types').PageLoad} */
export async function load({params, url, fetch}) {
    let slug = params.slug;

    let shareToken = url.searchParams.get('shareToken');
    let menuURL = `${PUBLIC_BASE_URL}/api/get/${slug}` + (shareToken ? `?shareToken=${shareToken}` : '');

    let uploadedFiles = [];
    const fileRes = await fetch(`${PUBLIC_BASE_URL}/api/file`, {
        credentials: 'include'
    });
    if (fileRes.ok) {
        let files = await fileRes.json();
        uploadedFiles = files.files;
    }


    const res = await fetch(menuURL, {
        credentials: 'include'
    });
    if (res.ok) {
        let menu = await res.json();
        return {menu: menu, uploads: uploadedFiles};
    }
    return {menu: null, uploads: uploadedFiles};
}