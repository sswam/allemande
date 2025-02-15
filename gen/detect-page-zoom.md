# How to detect page zoom level in all modern browsers using JavaScript ?

The article outlines methods to detect the page zoom level in modern browsers using JavaScript.

## Methods:
1. **Using outerWidth and innerWidth:**
- Subtract scrollbar width from outerWidth, divide by innerWidth to calculate zoom level.
- Example Syntax:
    ```javascript
    let zoom = ((window.outerWidth - 10) / window.innerWidth) * 100;
    ```

2. **Using clientWidth and clientHeight:**
- Get dimensions of the website using clientWidth and clientHeight properties.
- Example Syntax:
    ```javascript
    let zoom = body.clientWidth + "px x " + body.clientHeight + "px";
    ```

3. **Using window.devicePixelRatio:**
- Returns the ratio of physical pixels to CSS pixels.
- Example Syntax:
    ```javascript
    let value = window.devicePixelRatio;
    ```

Each method includes example code snippets and explanations for usage.
