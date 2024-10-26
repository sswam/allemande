from rope.base.project import Project
from rope.refactor.move import MoveModule

# Create a Rope project
project = Project('.')

# Add __version__ after imports
def add_version(project, module_path, version):
    module = project.get_resource(module_path)
    source = module.read()
    lines = source.split('\n')
    import_end = next(i for i, line in enumerate(lines) if not line.startswith('import') and not line.startswith('from'))
    lines.insert(import_end, f"\n__version__ = '{version}'\n")
    module.write('\n'.join(lines))

# Move symbols to different modules
def move_symbol(project, source_path, target_path, symbol):
    move = MoveModule(project, project.get_resource(source_path))
    changes = move.get_changes(target_path)
    project.do(changes)

# Usage examples
add_version(project, 'your_module.py', '1.0.0')
move_symbol(project, 'old_module.py', 'new_module.py', 'SymbolName')

project.close()
