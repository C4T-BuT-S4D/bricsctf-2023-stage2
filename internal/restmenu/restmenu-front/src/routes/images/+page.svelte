<script>
    import {PUBLIC_BASE_URL} from "$env/static/public";
    import {invalidateAll} from "$app/navigation";

    let error;
    let files;

    /** @type {import('./$types').PageData} */
    export let data;

    let uploaded = data.files;

    async function handleSubmit() {
        let formData = new FormData();
        formData.append('image', files[0]);

        const res = await fetch(`${PUBLIC_BASE_URL}/api/file/upload`, {
            method: 'POST',
            body: formData,
            credentials: "include",
        });
        if (res.ok) {
            await invalidateAll();
        } else {
            try {
                const json = await res.json();
                error = json.error;
            } catch (e) {
                error = await res.text();
            }
        }
    }

</script>
{#if error}
    <p style="color: red">{error}</p>
{/if}

<div class="grid">
    <div></div>
    <div>

        <h3>See images you uploaded:</h3>
        {#each uploaded as file}
            <div>
                {file}:<br>
            <img src="{PUBLIC_BASE_URL}/api/file/{file}" alt="{file}" height="100">

            </div>
        {/each}

        <div class="group">
            <input accept="image/png, image/jpeg" bind:files id="image" name="image" type="file"/>
        </div>

        <button on:click={handleSubmit}>Upload</button>
    </div>

    <div></div>


</div>
