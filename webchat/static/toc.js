function check_duplicate_ids(heading) {
    if (!heading.id) return;
    const existing = document.getElementById(heading.id);
    if (existing === heading) return;
    if (!existing) return;

    console.error(`Duplicate ID found: ${heading.id}`);
    let counter = 1;
    while (document.getElementById(`${heading.id}-${counter}`)) {
        counter++;
    }
    heading.id = `${heading.id}-${counter}`;
}

function find_current_list_state(toc) {
    let currentList = toc;
    let currentLevel = 1;
    while (currentList.lastElementChild?.lastElementChild?.tagName === 'UL') {
        currentList = currentList.lastElementChild.lastElementChild;
        currentLevel++;
    }
    return { currentList, currentLevel };
}

function ensure_list_level(targetLevel, currentList, currentLevel) {
    while (currentLevel < targetLevel) {
        const ul = document.createElement('ul');
        const li = document.createElement('li');
        li.textContent = '(No title - improper heading hierarchy)';
        console.error('Improper heading hierarchy - missing parent heading');
        li.appendChild(ul);
        currentList.appendChild(li);
        currentList = ul;
        currentLevel++;
    }
    while (currentLevel > targetLevel) {
        currentList = currentList.parentElement.parentElement;
        currentLevel--;
    }
    return currentList;
}

function toc_update(newMessageElement, tocElement) {
    const headings = newMessageElement.querySelectorAll('h1, h2, h3, h4, h5, h6');
    if (!headings.length) return;

    for (const heading of headings) {
        check_duplicate_ids(heading);
    }

    let { currentList, currentLevel } = find_current_list_state(tocElement);

    for (const heading of headings) {
        const level = parseInt(heading.tagName[1]);
        const li = document.createElement('li');
        const a = document.createElement('a');
        a.href = `#${heading.id}`;
        a.textContent = heading.textContent;
        li.appendChild(a);

        currentList = ensure_list_level(level, currentList, currentLevel);
        currentList.appendChild(li);
        currentLevel = level;
    }
}

function toc_rebuild(contentElement, tocElement) {
    tocElement.innerHTML = '';
    toc_update(contentElement, tocElement);
}
