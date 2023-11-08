<script>
    import '@picocss/pico'

    /** @type {import('./$types').LayoutData} */
    export let data;
</script>

<nav>
    <ul>
        <li><a href="/"><strong>RestMenu</strong></a></li>
    </ul>
    <ul>
        {#if data.user}
            <li><a href="/logout" role="button">Logout</a></li>
        {:else}
            <li><a href="/login" role="button">Sign in</a></li>
            <li><a href="/register" role="button" class="secondary">Sign Up</a></li>
        {/if}
    </ul>
</nav>

<main>
    <slot></slot>
</main>


