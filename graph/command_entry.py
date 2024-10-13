from tkinter import ttk

class CommandEntry(ttk.Entry):
    def __init__(self, parent, commands):
        super().__init__(parent)
        self.commands = commands

        # command shortcuts
        for command in list(commands.keys()):
            func = commands[command]
            while 1:
                command = command[:-1]
                if not command:
                    break
                try:
                    if commands[command]:
                        commands[command] = None
                    else:
                        break
                except KeyError:
                    commands[command] = func

        self.bind("<KeyPress-Return>", self.enter)

    def enter(self, event):
        words = self.get().split()
        if words:
            command, words = words[0], words[1:]
            self.delete(0, 'end')
            func = None
            try:
                func = self.commands[command]
                if func:
                    func(words)
                else:
                    self.error("<ambiguous command %s>" % command)
            except KeyError:
                self.error("<unknown command %s>" % command)

    def clear(self):
        self.delete(0, "end")

    def set(self, message):
        self.clear()
        self.insert(0, message)

    def error(self, error):
        self.set(error)
        self.bind("<KeyPress>", self.clear_error)

    def clear_error(self, event):
        self.clear()
        self.unbind("<KeyPress>")

__version__ = "0.1.2"
