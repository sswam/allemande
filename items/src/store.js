import { writable } from 'svelte/store';

//export const items = writable([]);

export const items = writable([
  { id: 1, status: 'todo', subject: 'Item 1', user: 'user1@example.com', size: 1 },
  { id: 2, status: 'doing', subject: 'Item 2', user: 'user2@example.com', size: 2 },
  { id: 3, status: 'done', subject: 'Item 3', user: 'user3@example.com', size: 3 }
]);

