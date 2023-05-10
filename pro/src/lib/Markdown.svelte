<script>
  import { onMount } from 'svelte';
//  const showdown = require('showdown');
//  import showdown from 'showdown';

//  console.log(showdown);

  let markdown = `# Hello, World!\n\nThis is a sample Markdown text.`;
  let html = '';

//  const converter = new Showdown.Converter();

  function convertMarkdownToHtml() {
//    html = converter.makeHtml(markdown);
    html = '<em>hello world</em>';
  }

  onMount(() => {
    convertMarkdownToHtml();
  });
</script>

<textarea bind:value="{markdown}" on:input="{convertMarkdownToHtml}" rows="5" cols="50"></textarea>

<div>
  <div class="markdown" svelte:html="{html}"></div>
</div>
