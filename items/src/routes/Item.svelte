<script>
  import { items } from '../store.js';
  export let item;

  function deleteItem() {
    items.update(items => items.filter(i => i.id !== item.id));
  }
</script>

<div class="kanban-item">
  <p>{item.subject}</p>
  <p>{item.user}</p>
  <p>{item.size}</p>
  <button on:click={deleteItem}>Delete</button>
</div>
