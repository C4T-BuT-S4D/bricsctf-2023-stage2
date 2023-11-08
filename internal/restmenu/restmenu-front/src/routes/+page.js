import {PUBLIC_BASE_URL} from '$env/static/public';

export async function load({fetch,  parent }) {
    const {user} = await parent();

    let menus = [];
    if (user) {
        const res = await fetch(`${PUBLIC_BASE_URL}/api/get`, {
            credentials: 'include'
        });
        menus = await res.json();
    }
    return {menus: menus};
}