<script>
    import {PUBLIC_BASE_URL} from "$env/static/public";

    /** @type {import('./$types').LayoutData} */
    export let data;

    let user = data.user;
    let menus = data.menus;
    let error;

    /** @param {{ currentTarget: EventTarget & HTMLFormElement}} event */
    async function handleSubmit(event) {
        const data = new FormData(event.currentTarget);

        let name = data.get('name');

        try {
            const res = await fetch(`${PUBLIC_BASE_URL}/api/create`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({name: name})
            });
            if (res.ok) {
                window.location.reload();
            } else {
                try {
                    error = await res.json().error;
                } catch (err) {
                    error = await res.text();
                }
            }
        } catch (err) {
            error = err.toString();
        }
    }
</script>
{#if error}
    <p style="color: red">{error}</p>
{/if}
<div class="grid">
    <div></div>
    <div>
        {#if user}
            <h4>Welcome back, "{user.username}". </h4>
            <p>Menus created by you:</p>
            <ul>
                {#each menus as menu}
                    <li><a href="/menu/{menu.id}">{menu.name}</a></li>
                {/each}
            </ul>
            <p>See your <a href="/images">uploaded images.</a></p>


            <div class="container">
                <h5>Create new menu for restaurant:</h5>
                <form method="post" on:submit|preventDefault={handleSubmit}>
                    <input type="text" name="name">
                    <input type="submit" value="Create">
                </form>
            </div>


        {:else}
            <h4>Welcome to RestMenu.</h4>
            <h5>Please Sign Up or Sign In to continue...</h5>
        {/if}

    </div>
    <div></div>
</div>
