Tasks list for building the visual task tracker app:

1. Design TSV file format
   - Define columns: ID, object type, additional info
   - Implement append-only structure for changes/deletions

2. Create local server component
   - Set up file read/write functionality
   - Implement data parsing and storage

3. Develop HTML UI
   - Design blank page layout
   - Create task representation (boxes/circles)
   - Implement line/arrow connections between tasks

4. Implement visual editing mode
   - Add/edit/delete tasks
   - Create/modify connections
   - Support nested graphs (sub-tasks)

5. Develop text editing mode
   - Display TSV content
   - Allow direct text editing
   - Sync changes with visual mode

6. Integrate graphviz-like storage
   - Convert TSV to graphviz format
   - Implement graphviz parsing

7. Create mode switching functionality
   - Toggle between visual and text modes
   - Ensure data consistency across modes

8. Implement relationship text annotations
   - Add text to lines/arrows
   - Store and display relationship information

9. Develop AI integration
   - Utilize command-line tools for code generation
   - Implement AI-assisted task management features

10. Test and refine
    - Ensure smooth transitions between modes
    - Verify data integrity and history tracking
    - Optimize UI/UX based on user feedback

