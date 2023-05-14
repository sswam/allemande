<script>
  import { items } from '../store.js';
//  let items = [
//    { id: 1, status: 'todo', subject: 'Item 1' },
//    { id: 2, status: 'doing', subject: 'Item 2' },
//    { id: 3, status: 'done', subject: 'Item 3' }
//  ];
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
  <div class="kanban-column">
    <h2>To Do</h2>
    {#each $items.filter(item => item.status === 'todo') as item}
      <div class="kanban-item">{item.subject}</div>
    {/each}
  </div>

  <div class="kanban-column">
    <h2>Doing</h2>
    {#each $items.filter(item => item.status === 'doing') as item}
      <div class="kanban-item">{item.subject}</div>
    {/each}
  </div>

  <div class="kanban-column">
    <h2>Done</h2>
    {#each $items.filter(item => item.status === 'done') as item}
      <div class="kanban-item">{item.subject}</div>
    {/each}
  </div>
</div>
