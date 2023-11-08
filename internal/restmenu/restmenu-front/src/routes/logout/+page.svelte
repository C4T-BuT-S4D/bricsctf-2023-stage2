<script>
    /** @type {import('./$types').LayoutData} */
    export let data;

    let user = data.user;
</script>

<p>Do you want to logout, "{user.username}"?</p>
<form method="post" action="/api/logout">
    <button type="submit">Logout</button>
</form>