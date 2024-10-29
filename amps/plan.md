Implementation approaches ordered by feasibility vs. effort:

1. Python Prototype
Pros:
- Fast iteration
- Rich ecosystem for parsing/UI
- Easy to experiment
Cons:
- Performance limitations
- Not suitable for final system
- GC overhead

2. Plain C Implementation
Pros:
- Full control
- No dependencies
- Optimal performance
Cons:
- More complex implementation
- Longer development time
- Manual memory management

3. Custom C Dialect
Pros:
- Familiar syntax
- Good performance
- Memory safety
Cons:
- Need to finish dialect first
- Two complex projects
- Bootstrap complexity

4. Self-Hosted
Pros:
- Dogfooding
- Pure implementation
- Conceptual elegance
Cons:
- Chicken-egg problem
- High initial complexity
- Slow early development

Recommended approach:
1. Python prototype for core concepts
2. C implementation of proven design
3. Optional migration to dialect/self-hosted

Critical first steps:
1. Relation representation
2. Pattern matching engine
3. Basic constraint solver
4. Simple visual editor
5. REPL environment

