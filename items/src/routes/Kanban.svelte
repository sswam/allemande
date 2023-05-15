<script>
  import { onMount } from 'svelte';
  import { items } from '../store.js';
  import Item from './Item.svelte';

  onMount(async () => {
    const response = await fetch('/api/items');
    if (response.ok) {
      const items = await response.json();
      items.set(items);
    } else {
      console.error(response.status);
    }
  });
//  let items = [
//    { id: 1, status: 'todo', subject: 'Item 1' },
//    { id: 2, status: 'doing', subject: 'Item 2' },
//    { id: 3, status: 'done', subject: 'Item 3' }
//  ];

  let draggedItem = null;

  function dragStart(event, item) {
    draggedItem = item;
  }

  function allowDrop(event) {
    event.preventDefault();
  }

  function drop(event, status) {
    event.preventDefault();
    draggedItem.status = status;

    // TODO: Call server function to update item
  }

</script>

<style>
  .kanban-board {
    display: flex;
    justify-content: space-around;
  }
  .kanban-column {
    border: 1px solid #ccc;
    padding: 1em;
    width: 30%;
  }
  .kanban-item {
    border: 1px solid #ccc;
    margin: 1em 0;
    padding: 1em;
  }
</style>

<div class="kanban-board">
  <div class="kanban-column" ondrop="{event => drop(event, 'todo')}" ondragover="{allowDrop}">
    <h2>To Do</h2>
    {#each $items.filter(item => item.status === 'todo') as item}
      <Item {item} />
    {/each}
  </div>

  <div class="kanban-column" ondrop="{event => drop(event, 'doing')}" ondragover="{allowDrop}">
    <h2>Doing</h2>
    {#each $items.filter(item => item.status === 'doing') as item}
      <Item {item} />
    {/each}
  </div>

  <div class="kanban-column" ondrop="{event => drop(event, 'done')}" ondragover="{allowDrop}">
    <h2>Done</h2>
    {#each $items.filter(item => item.status === 'done') as item}
      <Item {item} />
    {/each}
  </div>
</div>
