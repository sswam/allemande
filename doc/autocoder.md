# Auto Coder

## general considerations

  - option to run in a sandbox in case of catastrophic error or malicious AI
  - detect if AI is refusing to do something for 'ethical reasons' or whatever
  - track costs continually and set a limit for each job
  - avoid infinite loops
  - avoid degenerating loops where the code is getting worse
  - avoid null loops where the code is staying the same
  - avoid spinning the wheels where the code is not getting better or no more tests are passing for a while
  - avoid off-task changes to code
  - need to be able to apply patch-like changes from AI to the code
    - but probably don't try to persuade the AI to produce normal unified diff patches
    - not sure what format to use, function-at-a-time is probably okay
  - provide the AI only relevant info it needs to minimise input token costs
  - consider using RAG if needed, e.g. to find existing helper functions or tools among a large set

## find projects

  - find folders containing distinct projects, e.g. .git
  - sometimes there are sub-projects, find them too (probably not .git)
  - it can also create a new project, best to start with a simple version
    - need to be able to generate multiple files at once, and run setup commands
      - use markdown headings for filenames
      - use ```bash:run code blocks for commands to run
        - user confirms these by default!

## find source code

  - find all source code files in the project, based on git ls files if available, and carefully avoiding binary or data files
  - save to sources.txt
  - file types:
    - note file type of each file in sources.txt
    - create a file type summary (e.g., 60% Python, 30% JavaScript, 10% HTML

## dependencies

  - build an internal dependency graph, based on code in code_doc.py:
    - Save in 2-column TSV: file, dep file from the list (e.g. main.c	args/args.c)
  - build an external dependency graph at the file level:
    - Save in 4-column TSV. Extra columns are:
      - module name (for import)
      - location (either a directory under PYTHONPATH, a PyPI package name from the installation or from [requirements.txt or a provided requirements files list], or a URL if known from the installation or from requirements file/s.
  - We can do the internal and external dependecy graphs in one pass, with options for either / both.
  - build similar dependecy graphs at the symbol level, e.g. functions, classes, methods, global variables. This will require parsing unless we assume well-indented code and hack it. I think parsing is a good idea, but a 'hack' option would be good for unknown languages, something like ctags does.
  - Identify and highlight circular dependencies aka mutual dependencies
  - Generate a visual representation of the dependency graph (e.g., using GraphViz or mermaid)
    - display in the browser using DOM or SVG, allowing to adjust the layout and save it again
  - note that inter-language dependencies may exist, such as SQL views and stored procedures

## documentation

  - reimplement `code_doc` based on these graphs, to document code in the context of the documentation for its dependencies; i.e. we have split off the dependency functions
  - different types of documentation
    - specifications, with full API details, maybe including performance characteristics
    - API doc, full concise API description sufficient to use or re-implement all features
    - API cheatsheet, basic API description sufficient to use the main features
    - API overview, basic summary of API capabilities without enough info to use it
    - literate program, markdown literate program for the module in learning / expository order,
        e.g. `println("Hello, world")` before `public static void main(...)`.
  - check that the API doc is sufficiently precise to reimplement the function by asking an AI whether it is or not
  - Generate interactive documentation (e.g., Jupyter notebooks for Python projects)
  - Create documentation versioning to track changes over time, and commit to the repository

## comments and instrumentation

  - documentation enhancement: improve inline comments
    - add high-level comments like PyDoc for each module, class, method, and function
    - add necessary explantatory comments throughout the code using AI
  - add debug logging throughout the code using AI
  - do not change anything else in the code, don't even fix bugs or apparent syntax errors at this stage
  - a log can serve as a comment, so prefer not to do both in the same place
  - Implement structured logging for easier parsing and analysis
  - Add performance instrumentation (e.g., timing decorators) for key functions
    - do this in debug mode only, I think

## tests

  - find and start with existing tests, if available
  - write unit tests for each file / module including each public function, class or method
  - write integration tests in separate file/s for CLI usage, external API services such as web api, user web interaction, design visual quality (using AI or user assessment) etc
  - include performance tests where appropriate, including runtime, CPU usage, RAM usage, disk usage, etc; perhaps in a separate test file
  - note any tests that might incur costs such as very long runtime, or use of paid APIs including AI APIs, these should not run by default
  - check that the tests pass, if not iterate changing code and/or tests until the tests pass. Enable debugging if needed. A configurable limit of how many tries. The process can add debugging logs.
  - implement property-based testing for suitable functions
    - Property-based testing is a testing technique where instead of writing specific test cases, you define properties that your code should always satisfy. The testing framework then generates random inputs to test these properties, automatically finding edge cases and unexpected scenarios. This approach can uncover bugs that traditional unit tests might miss and provides broader test coverage with less manually written code.
  - create mock objects for external dependencies to improve test isolation
  - measure test coverage

### improve tests

  - test coverage expansion: generate additional unit tests to improve coverage:
    - check that the tests are comprehensive by asking an AI whether they are or not; if not, improve them; iterative improvement without going too far
  - the AI might also suggest removing redundant or pointless tests
  - Implement mutation testing to evaluate test suite effectiveness
    - Mutation testing is a software testing technique that involves introducing small changes (mutations) to the source code and running tests to see if they detect these changes. It assesses the quality and effectiveness of existing test suites by measuring their ability to identify intentionally introduced faults.
  - Generate edge case tests based on static analysis of the code

## refactoring

  - improve code quality or performance without changing functionality or API; focus on simple, clear, general code
    - other ideas from Pracice of Programming, and expert sources
    - simple, clear readable code is the most important thing, even more important than correctness
    - split out helper functions / classes
    - use existing modules and helper functions / classes
  - option to improve API, will also need to adjust the tests and any modules that use this one
    - write a migration guide and preferably a migration script using ast for clients of the refactored module
  - inter-file refactoring, e.g. combining files, splitting files, moving files
    - can do this based on the hierarchy (sources.txt) along with the API doc of each file
  - implement automated code formatting using language-specific tools (e.g., Black for Python)
    - especially important for braced languages which may be formatted very poorly in theory at least
    - also consider rearrangement tools such as isort
  - add type annotations where beneficial
  - dependency optimization: analyze and minimize imports/dependencies
    - avoid tight coupling, and use dependency injection as much as possible
    - we aim for highly-modular code, where each module is simple and can stand alone
  - design pattern application: identify and apply appropriate design patterns.
  - async code: use asyncio to enable efficient coroutines
    - this is a breaking change, would need to adjust client users
    - or keep the old sync interface too?
  - parallelization: identify opportunities for concurrent execution.
  - memory optimization: suggest more efficient data structures or memory usage patterns.
  - code smell detection and removal: identify and fix common code smells.
  - naming convention enforcement: ensure consistent and meaningful naming across the codebase.
    - e.g. my toolkit program names; will need to know the deps though
  - error handling improvement: enhance exception handling and error reporting.
  - implement lazy loading patterns for resource-intensive operations
  - refactor to use more immutable data structures where appropriate
  - ***CRAZY*** implement mathematics in separate graph-based math files,
    and compile it into the target language, and into TeX for documentation

## profiling and performance

  - performance profiling and optimization: analyze runtime behavior and suggest optimizations.
  - implement caching strategies for frequently accessed data or computation results
  - analyze and optimize database queries (if applicable)

## bug-detection

  - run pylint or similar to find possible syntactic bugs or bad practises
    - can fix the issues, or add a comment to disable linting for that case
  - Perform static type checking (e.g. mypy)
  - AI code review / inspection to look for bugs
    - this may work better function by function rather than throwing a wall of text at it
  - run the tests
  - find bugs (or receive bug reports), add failing regression tests, fix the bugs, ensure tests pass

## bug-fixing

  - security vulnerability detection and patching: identify and fix potential security issues.
    - include failing regression tests
  - debug using logs
    - add logging to help
  - debug using an interactive debugger?
    - this might be very difficult to implement
    - at least run via a debugger to get proper SEGV diagnostic information
      - core dumps
    - AI could prepare a debugger script in advance
  - debug using valgrind, for C/C++ code
  - possibility of bugs in dependent code or  3rd-party modules
  - Implement automated fuzzing to discover potential edge case bugs
  - create a bug triage system to prioritize and categorize reported issues

## Triage

  - assess priority of reported bugs and requested features
    - typically bugs come first
  - file some bugs or features under wontfix / wontdo
    - simplicity is important, featuritis is bad
    - we can implement custom tools for individual clients or users without hacking the main code

## Features

  - internationalization: prepare code for multi-language support.
  - accessibility: refactor ui code to enhance accessibility features.
  - generality: make code more general, with a compatible API, or with an improved API
  - implement feature flags for gradual rollout of new features
  - create an extensibility framework (e.g., plugin system) if appropriate for the project
