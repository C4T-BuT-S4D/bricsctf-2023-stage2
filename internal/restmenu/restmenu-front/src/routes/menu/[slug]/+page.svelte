<script>
    import SvelteMarkdown from 'svelte-markdown'
    import {PUBLIC_BASE_URL} from "$env/static/public";
    import {invalidateAll} from "$app/navigation";

    /** @type {import('./$types').PageData} */
    export let data;

    let menu = data.menu;
    let uploaded = data.uploads;

    let categories = menu.categories;

    let error;

    function addCategory() {
        categories = [...categories, {
            name: 'Hacker food',
            items: []
        }];
    }

    function addItem(categoryIndex) {
        categories[categoryIndex].items = [...categories[categoryIndex].items, {
            name: 'PWN beer',
            price: 1337,
            description: "Really great taste",
            image: null,
        }];
    }

    async function handleSave() {
        let request = {
            menu: {
                id: menu.id,
                name: menu.name,
                categories: categories,
                author: menu.author,
                shared: menu.shared,
                shareToken: menu.shareToken,
                markdown: menu.markdown,
            }
        }
        try {
            const res = await fetch(`${PUBLIC_BASE_URL}/api/update`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify(request)
            });
            if (res.ok) {
                menu = await res.json();

                await invalidateAll();
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

{#if !menu }
    <h4>Menu not found</h4>
{:else}
    {#key menu.markdown}
        <SvelteMarkdown source={menu.markdown}/>
    {/key}
    <hr>
    <div class="grid">
        {#if menu.shared}
            <div>
                <a href="/menu/{menu.id}">Public link</a>
            </div>
            <div>
                <a href="/api/render/{menu.id}">Get PDF</a>
            </div>
        {:else }
            <div>
                <a href="/menu/{menu.id}?shareToken={menu.shareToken}">Link to share draft</a>
            </div>
            <div>
                <a href="/api/render/{menu.id}?shareToken={menu.shareToken}">Get PDF draft</a>
            </div>
        {/if}
    </div>

    {#if data.user && menu.author === data.user.id}
        <hr>

        <div class="grid">
            <div></div>
            <div>
                <label>
                    Name:
                    <input bind:value={menu.name} placeholder="enter restaurant name">
                </label>

                <div style="padding-left: 5em">
                    {#each categories as category, categoryIndex}
                        <div>
                            <label>
                                Category name:
                                <input type="text" bind:value={category.name} placeholder="enter category name">
                            </label>

                            <div style="padding-left: 5em">
                                {#each category.items as item}
                                    <div>
                                        <label>
                                            Item name:
                                            <input type="text" bind:value={item.name} placeholder="enter item name">
                                        </label>
                                        <label>
                                            Price:
                                            <input type="number" bind:value={item.price} placeholder="enter item price">
                                        </label>
                                        <label>
                                            Description:
                                            <input type="text" bind:value={item.description}
                                                   placeholder="enter item price">
                                        </label>
                                        <select bind:value={item.image}>
                                            <option value={null}>No image</option>
                                            {#each uploaded as image}
                                                <option value={image}>{image}</option>
                                            {/each}
                                        </select>
                                        {#if item.image}
                                            <img src={`${PUBLIC_BASE_URL}/api/file/${item.image}`} alt="{item.image}"
                                                 height="100"/>
                                            <br>
                                        {/if}
                                        <a href="#"
                                           on:click|preventDefault={() => category.items = category.items.filter(i => i !== item)}>Remove
                                            Item</a>
                                    </div>
                                {/each}
                            </div>
                            <p><a href="#" on:click|preventDefault={() => addItem(categoryIndex)}>Add Item</a></p>
                            <a href="#"
                               on:click|preventDefault={() => categories = categories.filter(c => c !== category)}>Remove
                                Category</a>
                        </div>
                    {/each}
                </div>
                <p><a href="#" on:click|preventDefault={addCategory}>Add Category</a></p>


                <label>
                    Public:
                    <input type="checkbox" bind:checked={menu.shared}/>
                </label>

                <button on:click={handleSave}>Save</button>
            </div>
            <div></div>
        </div>
    {/if}


{/if}
