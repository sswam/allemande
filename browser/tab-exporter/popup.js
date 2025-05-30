const browserAPI = (typeof browser !== 'undefined' ? browser : chrome);

document.getElementById('export').addEventListener('click', () => {
  browserAPI.tabs.query({currentWindow: true}, (tabs) => {
    const tabData = tabs.map(tab => ({
      url: tab.url,
      title: tab.title
    }));

    // For TSV
    // const tsv = ['URL\tTitle']
     const tsv = tabData.map(tab => `${tab.url}\t${tab.title}`)
      .join('\n');

    // For JSON
    // const json = JSON.stringify(tabData, null, 2);

    // Save file
    const blob = new Blob([tsv], {type: 'text/tab-separated-values'});
    const url = URL.createObjectURL(blob);
    browserAPI.downloads.download({
      url: url,
      filename: 'tabs.tsv'
    });
    URL.revokeObjectURL(url);
  });
});
