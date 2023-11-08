<script>
    import {invalidateAll, goto} from '$app/navigation';
    import {PUBLIC_BASE_URL} from "$env/static/public";

    /** @type {any} */
    let error;

    /** @param {{ currentTarget: EventTarget & HTMLFormElement}} event */
    async function handleSubmit(event) {
        const data = new FormData(event.currentTarget);

        let username = data.get('username');
        let password = data.get('password');

        try {
            const res = await fetch(`${PUBLIC_BASE_URL}/api/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({username: username, password: password})
            });
            if (res.ok) {
                await goto('/', {invalidateAll: true});
                return;
            }
            error = await res.text();
            try {
                error = JSON.parse(error).error;
            } catch (err) {
                // ignore
            }
        } catch (err) {
            error = err.toString();
        }
        await invalidateAll();
    }
</script>

<div class="grid">
    <div></div>
    <div>

        <h3>Let's login!</h3>
        {#if error}
            <p style="color: red">{error}</p>
        {/if}

        <form method="POST" on:submit|preventDefault={handleSubmit}>
            <div class="grid">
                <div>
                    <label for="username">
                        Username
                        <input type="text" id="username" name="username" placeholder="user">
                    </label>
                </div>
                <div>
                    <label for="password">
                        Password
                        <input type="password" id="password" name="password" placeholder="password">
                    </label>
                </div>
            </div>
            <input type="submit" value="Login">
        </form>
    </div>

    <div></div>


</div>
