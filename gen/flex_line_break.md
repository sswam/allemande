.row_wrap {
	display: flex;
	flex-flow: row wrap;
	gap: var(--pad);
	align-content: flex-start;
}

Is there a way to put a 'break' among the items, so a certain item will start a new (wrapped) line? Or just use multiple parent containers?

## Forcing a Flex Line Break

Yes! You can force a line break in a flex row wrap layout without multiple containers. Here are the options:

### Option 1: Full-Width Break Element
Insert an empty element that spans the full width:

```css
.break {
	width: 100%;  /* forces wrap to next line */
	height: 0;    /* no visual space added */
}
```

```html
<div class="row_wrap">
	<div>Item 1</div>
	<div>Item 2</div>
	<div class="break"></div>  <!-- Line break here -->
	<div>Item 3</div>
	<div>Item 4</div>
</div>
```

---

### Option 2: CSS-Only on a Specific Item
Target the item that should start a new line:

```css
.new-line {
	flex-basis: 100%; /* pushes this item to its own line */
	/* or */
	width: 100%;
}
```

---

### Option 3: Using `::before` / `::after` (no extra HTML)

```css
/* Break before the 3rd item */
.row_wrap > :nth-child(3) {
	flex-basis: 100%;
	height: 0;
}
```

> ⚠️ This makes the 3rd *child* take full width — works as a break only if that child has `height: 0` and no content.

---

### Option 4: On the Item Itself (cleanest semantic approach)

```css
.row_wrap {
	display: flex;
	flex-flow: row wrap;
	gap: var(--pad);
	align-content: flex-start;
}

.break-before {
	flex-basis: 100%; /* no content, just pushes next items down */
	height: 0;
}
```

```html
<div class="row_wrap">
	<div>Item 1</div>
	<div>Item 2</div>
	<div class="break-before">Item 3</div> <!-- starts new line -->
	<div>Item 4</div>
</div>
```

---

### Comparison

| Method | Pros | Cons |
|--------|------|------|
| Break element | Simple, reusable | Extra HTML |
| `flex-basis: 100%` on item | No extra HTML | Changes item width |
| `nth-child` pseudo | No extra HTML | Fragile, positional |
| Multiple containers | Most semantic | More markup |

**Recommended:** The **empty break element** is the most flexible and explicit approach for dynamic layouts.
