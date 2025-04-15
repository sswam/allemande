## Esprima Cheat-Sheet

### Overview
- **Esprima**: JavaScript parser for lexical and syntactical analysis.
- Does **not** support variations like TypeScript or Flow.

### Supported Environments
- Modern Browsers: Edge, Firefox, Chrome, Safari
- Legacy Browsers: IE 10+
- **Node.js**: v4 or later
- Other JS engines: Rhino, Nashorn

### Installation (Node.js)
1. Install Node.js (includes npm).
2. Install Esprima:
   ```bash
   npm install esprima
   ```

### Basic Usage (Node.js REPL)
```javascript
var esprima = require('esprima');
var AST = esprima.parseScript('var answer = 42');
console.log(AST);
```

### Browser Usage
- Load through a `<script>` tag:
  ```html
  <script src="https://unpkg.com/esprima@~4.0/dist/esprima.js"></script>
  ```
  
- Use with AMD:
  ```javascript
  require(['esprima'], function (parser) {
      var syntax = parser.parse('var answer = 42');
      console.log(JSON.stringify(syntax, null, 4));
  });
  ```

### Parsing Functions
- **Scripts**: `esprima.parseScript(input, config, delegate)`
- **Modules**: `esprima.parseModule(input, config, delegate)`

**Arguments**:
- `input`: JavaScript code string.
- `config`: Optional parsing behavior customization.
- `delegate`: Optional callback for each node.

### Parsing Configuration Options
| Name      | Type     | Default | Description                                     |
|-----------|----------|---------|-------------------------------------------------|
| `jsx`     | Boolean  | false   | Support JSX syntax                              |
| `range`   | Boolean  | false   | Annotate nodes with index-based location        |
| `loc`     | Boolean  | false   | Annotate nodes with line/column-based location  |
| `tolerant`| Boolean  | false   | Tolerate some syntax errors                     |
| `tokens`  | Boolean  | false   | Collect every token during parsing               |
| `comment` | Boolean  | false   | Collect all comments                             |

### Error Handling
- Invalid input throws an exception.
- Use `tolerant: true` to collect errors without stopping the parser.

### Tokenization
- **Function**: `esprima.tokenize(input, config)`
- Returns an array of tokens with properties:
  - `type`: Token type
  - `value`: Token value

### Token Configuration Options
- Similar to parse config but applies to tokens:
| Name      | Type     | Default | Description                                     |
|-----------|----------|---------|-------------------------------------------------|
| `range`   | Boolean  | false   | Add start/end position to each token           |
| `loc`     | Boolean  | false   | Add line/column information                     |
| `comment` | Boolean  | false   | Include comments in output                      |

### Syntax Tree Format
- Based on ESTree specification, nodes have:
```javascript
interface Node {
  type: string;
  range?: [number, number];
  loc?: SourceLocation;
}
```
### Key Node Types
- **Expressions**: `Identifier`, `Literal`, `FunctionExpression`, `CallExpression`, etc.
- **Statements**: `IfStatement`, `ForStatement`, `WhileStatement`, etc.
- **Declarations**: `VariableDeclaration`, `FunctionDeclaration`

### Example: Parse and Remove Console Calls
```javascript
const esprima = require('esprima');
function removeConsoleCalls(source) {
    //... logic to parse and remove console calls
}
```

### Additional Features
- **Location Information**: Use `range` and `loc` for detailed node/token info.
- **Comment Collection**: Enable `comment` to include comments in results.

### Example: Syntax Highlighting
```javascript
const esprima = require('esprima');
const tokens = esprima.tokenize(source, { range: true });
// Color code identifiers in source based on token positions
```

### Important Notes
- Use `parseScript` for standard scripts and `parseModule` for ES2015 modules.
- Error handling and tolerance configurations allow more flexibility when dealing with code snippets. 

For more advanced usage, refer to Esprima documentation and specific syntax tree formats described in their appendices.

