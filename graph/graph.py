#!/usr/bin/env python3

"""
This module provides a simple graph editor with a graphical user interface.
It allows users to create, edit, and manipulate nodes and arcs in a graph structure.
"""

from tkinter import *
from tkinter import Canvas
from tkinter import ttk
from ttkthemes import ThemedTk
import sys
from math import sqrt, sin, cos, tan, atan, atan2, pi, floor

from ally import main, logs

from command_entry import CommandEntry

__version__ = "0.1.1"  # Assuming the previous version was 0.1.0

logger = logs.get_logger()


strip = str.strip
split = str.split
join = str.join


class Space:
    def __init__(self):
        self.nodes = []
    def add_node(self, node):
        self.nodes.append(node)
    def remove_node(self, node):
        self.nodes.remove(node)
    def write(self, filename):
        f=open(filename, "w")
        n = 1
        ids = {}
        for node in self.nodes:
            f.write(join([".", node.name, str(n), str(node.x), str(node.y), str(node.r)], "\t")+"\n")
            ids[node] = str(n)
            n = n + 1
        for node in self.nodes:
            for arc in node.arcs_out:
                f.write(join(["-", arc.name, ids[arc.source], ids[arc.target], str(arc.bend_a)], "\t")+"\n")
        f.close()
    def read(self, filename):
        f=open(filename, "r")
        line = f.readline()
        nodes = {}
        while line:
            fields = split(strip(line), "\t")
            type, name = fields[0:2]
            rest = fields[2:]
            if type == ".":
                n, x, y, r = rest
                n = int(n); x = float(x); y = float(y); r = float(r)
                nodes[n] = Node(self, x, y, r, name)
            elif type == "-":
                n1, n2, bend = rest
                n1 = int(n1); n2 = int(n2); bend = float(bend)
                Arc(nodes[n1], nodes[n2], bend=bend, name=name)
            else:
                editor.entry.error("bad type in file")
            line = f.readline()
        f.close()
    def clear(self):
        for node in self.nodes[:]:
            node.delete()
    def update_arcs_and_labels(self):
        for node in self.nodes:
            for arc in node.arcs_out:
                arc.update_fast();
        for node in self.nodes:
            node.update_label()


class Controller:
    def space_click(self, space, x, y):
        pass
    def space_drag(self, space, x, y):
        pass
    def space_release(self, space, x, y):
        pass
    def node_click(self, node, x, y):
        self.space_click(editor.space, x, y)
    def node_drag(self, node, x, y):
        self.space_drag(editor.space, x, y)
    def node_release(self, node, x, y):
        self.space_release(editor.space, x, y)
    def arc_click(self, arc, x, y):
        pass
    def arc_drag(self, arc, x, y):
        pass
    def arc_release(self, arc, x, y):
        pass
    def label_click(self, arc, x, y):
        pass
    def label_drag(self, arc, x, y):
        pass
    def label_release(self, arc, x, y):
        pass


class Pan(Controller):
    def space_click(self, space, x, y):
        self.drag_x = x
        self.drag_y = y
    def space_drag(self, space, x, y):
        dx = x - self.drag_x
        dy = y - self.drag_y
        for node in editor.space.nodes:
            node.space_translate(dx, dy)
            for arc in node.arcs_out:
                arc.space_translate(dx, dy)
        self.drag_x = x
        self.drag_y = y


class Zoom(Controller):
    def space_click(self, space, x, y):
        self.drag = complex(x, y)
    def space_drag(self, space, x, y):
        drag_to = complex(x, y)
        o = complex(canvas.winfo_width()/2,canvas.winfo_height()/2)
        d0 = self.drag - o
        d1 = drag_to - o
        factor = d1 / d0
        rscale = abs(factor)
        for node in editor.space.nodes:
            p = complex(node.x, node.y)
            p = (p - o) * factor + o
            node.move_to_fast(p.real, p.imag)
# uncomment the following three lines for a different sort of zoom
#            node.resize(node.r * rscale)
#            for arc in node.arcs_out:
#                arc.resize(arc.r * rscale)
        editor.space.update_arcs_and_labels()
        self.drag = drag_to


class Move(Pan):
    def node_click(self, node, x, y):
        self.drag_x = node.x - x
        self.drag_y = node.y - y
    def node_drag(self, node, x, y):
        node.move_to(x + self.drag_x, y + self.drag_y)
    def arc_drag(self, arc, x, y):
        arc.bend_to(x, y)


class Delete(Pan):
    def node_click(self, node, x, y):
        node.delete()
    def arc_click(self, arc, x, y):
        arc.delete()


class Add(Move):
    def space_click(self, space, x, y):
        entry = editor.entry
        Node(space, x, y, name=entry.get())
        entry.clear()
    def space_drag(self, space, x, y):
        pass
    def node_click(self, node, x, y):
        self.node_from = node
        self.node_temp = Node(space, x, y, 0)
        Arc(self.node_from, self.node_temp)
    def node_drag(self, node, x, y):
        self.node_temp.move_to(x, y)
    def node_release(self, node, x, y):
        entry = editor.entry
        self.node_temp.delete()
        # evil Tkinter is broken w.r.t. find!
        id, = editor.canvas.find_closest(x, y)
        node_to = Node.node_by_id.get(id)
        if node_to and node_to != self.node_from:
            Arc(self.node_from, node_to, name=entry.get())
        entry.clear()
        self.node_from = self.node_temp = None


class Size(Move):
    def node_click(self, node, x, y):
        pass
    def node_drag(self, node, x, y):
        dx = x - node.x
        dy = y - node.y
        r = sqrt(dx*dx + dy*dy)
        node.resize(r)


class Name(Controller):
    def node_click(self, node, x, y):
        entry = editor.entry
        node.set_name(entry.get())
        entry.clear()
    def arc_click(self, arc, x, y):
        entry = editor.entry
        arc.set_name(entry.get())
        entry.clear()


class Node:
    node_by_id: dict[int, 'Node'] = {}
    def __init__(self, space, x, y, r=10, name=""):
        self.space = space
        self.space.add_node(self)
        self.arcs_out = []
        self.arcs_in = []
        self.x = x
        self.y = y
        self.r = r
        self.canvasitem = canvas.create_oval(x-r, y-r, x+r, y+r, outline=editor.fg, fill=editor.bg)
        canvas.tag_bind(self.canvasitem, "<Button-1>", self.click)
        canvas.tag_bind(self.canvasitem, "<Button1-Motion>", self.drag)
        canvas.tag_bind(self.canvasitem, "<ButtonRelease-1>", self.release)
        Node.node_by_id[self.canvasitem] = self
        self.label = canvas.create_text(0, 0)
        self.label_x = self.label_y = 0
        self.name = name
        self.update_label()
    def delete(self):
        for arc in self.arcs_out + self.arcs_in:
            arc.delete()
        canvas.delete(self.canvasitem)
        canvas.delete(self.label)
        self.space.remove_node(self)
    def add_out(self, arc):
        self.arcs_out.append(arc)
    def add_in(self, arc):
        self.arcs_in.append(arc)
    def remove_out(self, arc):
        self.arcs_out.remove(arc)
        self.update_label()
    def remove_in(self, arc):
        self.arcs_in.remove(arc)
        self.update_label()
    def click(self, event):
        editor.ignore_events()
        editor.controller.node_click(self, event.x, event.y)
    def drag(self, event):
        editor.controller.node_drag(self, event.x, event.y)
    def release(self, event):
        editor.controller.node_release(self, event.x, event.y)
    def move_to(self, x, y):
        self.move_by(x - self.x, y - self.y)
    def move_by(self, dx, dy):
        self.move_by_fast(dx, dy)
        for arc in self.arcs_out + self.arcs_in:
            arc.update()
        self.update_label()
    def move_to_fast(self, x, y):
        self.move_by_fast(x - self.x, y - self.y)
    def move_by_fast(self, dx, dy):
        self.x = self.x + dx
        self.y = self.y + dy
        canvas.move(self.canvasitem, dx, dy)
    def space_translate(self, dx, dy):
        self.move_by_fast(dx, dy)
        self.label_x = self.label_x + dx
        self.label_y = self.label_y + dy
        canvas.move(self.label, dx, dy)
    def arc_point(self, x1, y1):
        r = self.r + 2
        x = self.x + r * x1
        y = self.y + r * y1
        return x, y
    def resize(self, r):
        self.r = r
        canvas.coords(self.canvasitem, self.x-self.r, self.y-self.r, self.x+self.r, self.y+self.r)
        for arc in self.arcs_out + self.arcs_in:
            arc.update()
        self.update_label()
    def set_name(self, name):
        self.name = name
        self.update_label()
    def update_label(self):
        # calculate best position for label - the middle of the widest
        # angle between arcs
        angles = []
        for arc in self.arcs_out:
            angles.append(arc.angle_at_source_node())
        for arc in self.arcs_in:
            angles.append(arc.angle_at_target_node())
        angles.sort()
        if len(angles) == 0:
            a = 45.0
        elif len(angles) == 1:
            a = angles[0] + 180
        else:
            besti = 0
            besta = angles[1] - angles[0]
            for i in range(1,len(angles)-1):
                a = angles[i+1] - angles[i]
                if a > besta:
                    besta = a
                    besti = i
            if angles[0]+360 - angles[-1] > besta:
                a = (angles[0]+360 + angles[-1]) / 2
            else:
                a = (angles[besti+1] + angles[besti]) / 2
        if a > 180:
            a = a - 360
        # self.label_a = a
        i = int(floor(a / 45 + 0.5))
        anchor = ["s", "sw", "w", "nw", "n", "ne", "e", "se"][i % 8]
        canvas.itemconfig(self.label, fill=editor.fg, text=self.name, anchor=anchor)
        a = a / 180 * pi
        x = sin(a) * (self.r + 2) + self.x
        y = -cos(a) * (self.r + 2) + self.y
        canvas.move(self.label, x - self.label_x, y - self.label_y)
        self.label_x = x
        self.label_y = y


class Arc:
    def __init__(self, source, target, r=1, bend=0.0, name=""):
        self.source = source
        self.target = target
        self.source.add_out(self)
        self.target.add_in(self)
        self.r = r
        self.bend_a = bend
        self.canvasitem = canvas.create_line(0,0, 0,0, 0,0, fill=editor.fg, arrow="last", arrowshape=(r*4, r*5, r), smooth=1, width=r)
        canvas.tag_bind(self.canvasitem, "<Button-1>", self.click)
        canvas.tag_bind(self.canvasitem, "<Button1-Motion>", self.drag)
        canvas.tag_bind(self.canvasitem, "<ButtonRelease-1>", self.release)
        self.label = canvas.create_text(0, 0)
        self.label_x = self.label_y = 0
        self.name = name
        self.update()
    def delete(self):
        self.source.remove_out(self)
        self.target.remove_in(self)
        canvas.delete(self.canvasitem)
        canvas.delete(self.label)
    def update_fast(self):
        canvas.itemconfig(self.canvasitem, width=self.r, arrowshape=(6, 10, 2))
        s = complex(self.source.x, self.source.y)
        t = complex(self.target.x, self.target.y)
        d = t - s
        a = self.bend_a / 180 * pi
        m = complex(1, tan(a)*2) * d / 2 + s
        v0 = m - s ; v0 = v0 / abs(v0)
        v1 = m - t ; v1 = v1 / abs(v1)
        sx, sy = self.source.arc_point(v0.real, v0.imag)
        tx, ty = self.target.arc_point(v1.real, v1.imag)
        self.sa = atan2(v0.real, -v0.imag)*180/pi
        self.ta = atan2(v1.real, -v1.imag)*180/pi
        canvas.coords(self.canvasitem, sx, sy, m.real, m.imag, tx, ty)
        # update label position
        a = atan2(ty-sy,tx-sx) * 180 / pi
        if self.bend_a > 0:
            k = 1 ; a = a + 180
        else:
            k = -1
        p1 = complex(0, k) * d
        mid = (s + t) / 2
        p = (m - mid) / 1.9
        p = p + p1/abs(p1)*6 + mid
        x = p.real ; y = p.imag
        i = int(floor(a / 45 + 0.5))
        anchor = ["s", "sw", "w", "nw", "n", "ne", "e", "se"][i % 8]
        canvas.itemconfig(self.label, fill=editor.fg, text=self.name, anchor=anchor)
        canvas.move(self.label, x - self.label_x, y - self.label_y)
        self.label_x = x
        self.label_y = y
    def update(self):
        self.update_fast()
        self.source.update_label()
        self.target.update_label()
    def space_translate(self, dx, dy):
        canvas.move(self.canvasitem, dx, dy)
        self.label_x = self.label_x + dx
        self.label_y = self.label_y + dy
        canvas.move(self.label, dx, dy)
    def angle_at_source_node(self):
        return self.sa
    def angle_at_target_node(self):
        return self.ta
    def click(self, event):
        editor.ignore_events()
        editor.controller.arc_click(self, event.x, event.y)
    def drag(self, event):
        editor.controller.arc_drag(self, event.x, event.y)
    def release(self, event):
        editor.controller.arc_release(self, event.x, event.y)
    def bend_to(self, x, y):
        m = complex(x, y)
        s = complex(self.source.x, self.source.y)
        t = complex(self.target.x, self.target.y)
        d = t - s
        self.bend_a = 180/pi * atan(((m - s) / d * 2).imag)
        self.update()
        self.source.update_label()
        self.target.update_label()
    def resize(self, r):
        self.r = r
        self.update()
    def set_name(self, name):
        self.name = name
        self.update()


class Editor:
    def __init__(self):
        self.bg: str = "black"
        self.fg: str = "white"

        root = ThemedTk()
        style = ttk.Style(root)

        # Create a custom theme
        style.theme_create("BlackWhite", parent="alt", settings={
            "TLabel": {"configure": {"background": "black", "foreground": "white"}},
            "TButton": {"configure": {"background": "black", "foreground": "white"}},
            "TEntry": {
                "configure": {
                    "fieldbackground": "black",
                    "foreground": "white",
                    "insertcolor": "white",  # cursor color
                    "selectbackground": "gray",  # selection highlight color
                    "selectforeground": "white"  # selected text color
                }
            },
            "TFrame": {"configure": {"background": "black", "borderwidth": 0}},
        })

        style.theme_use("BlackWhite")

        # Configure the root window
        root.configure(bg="black")

        self.frame = ttk.Frame(root)
        self.frame.master.title("graph editor")
        self.frame.pack(fill=BOTH, expand=True)
        Pack.config(self.frame)
        # entry
        commands: dict[str, Callable] = {
            "add": self.command_add,
            "delete": self.command_delete,
            "quit": self.command_quit,
            "pan": self.command_pan,
            "zoom": self.command_zoom,
            "move": self.command_move,
            "size": self.command_size,
            "name": self.command_name,
            "write": self.command_write,
            "read": self.command_read,
            "clear": self.command_clear,
        }
        self.entry = CommandEntry(self.frame, commands)
        self.entry.pack(fill=X, expand=N, side=BOTTOM)
        # canvas
        self.canvas = Canvas(self.frame, width=640, height=480, background=self.bg, highlightthickness=0, bd=0)
        self.canvas.pack(fill=BOTH, expand=Y, side=TOP)
        self.canvas.bind("<Button-1>", self.click)
        self.canvas.bind("<Button1-Motion>", self.drag)
        self.canvas.bind("<ButtonRelease-1>", self.release)
        self.ignore: int = 0
        self.space = Space()
        self.add = Add()
        self.controller: Controller = self.add
        self.move = Move()
        self.pan = Pan()
        self.zoom = Zoom()
        self.size = Size()
        self.name = Name()
        self.delete = Delete()
        self.filename: str | None = None
    def command_add(self, words):
        self.controller = self.add
    def command_delete(self, words):
        self.controller = self.delete
    def command_move(self, words):
        self.controller = self.move
    def command_pan(self, words):
        self.controller = self.pan
    def command_zoom(self, words):
        self.controller = self.zoom
    def command_size(self, words):
        self.controller = self.size
    def command_name(self, words):
        self.controller = self.name
    def set_filename(self, words):
        if len(words) == 1:
            self.filename = words[0]
        elif len(words) > 1:
            self.entry.error("too many filenames!")
            return None
        elif len(words) == 0 and not self.filename:
            self.entry.error("no filename")
        return self.filename
    def command_write(self, words):
        if self.set_filename(words):
            space.write(self.filename)
    def command_clear(self, words):
        space.clear()
    def command_read(self, words):
        if self.set_filename(words):
            space.read(self.filename)
    def command_quit(self, words):
        sys.exit(0)
    def click(self, event):
        if not self.ignore:
            self.controller.space_click(self.space, event.x, event.y)
    def drag(self, event):
        if not self.ignore:
            self.controller.space_drag(self.space, event.x, event.y)
    def release(self, event):
        if self.ignore:
            self.ignore = 0
        else:
            self.controller.space_release(self.space, event.x, event.y)
    def ignore_events(self):
        self.ignore = 1


editor: Editor = None
frame: Frame = None
space: Space = None
canvas: Canvas = None


def graph_editor(file: str|None = None):
    global editor, frame, space, canvas
    if file:
        editor.command_read(file)
    editor = Editor()
    frame = editor.frame
    space = editor.space
    canvas = editor.canvas

    frame.mainloop()

if __name__ == "__main__":
    main.go(graph_editor)
