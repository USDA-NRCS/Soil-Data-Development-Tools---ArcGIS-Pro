# tk_BalloonText.py
#
# Example of help message that displays on mouse hover.

import tkinter as tk
import tkinter.tix as tix


class Balloon(tix.Balloon):

    # A modified tix popup balloon (to change the default delay, bg and wraplength)

    init_after = 1250  # Milliseconds
    wraplength = 300  # Pixels

    def __init__(self, master):
        bg = window.cget("bg")
        # Call the parent
        super().__init__(master, initwait=self.init_after)
        # Change background colour
        for i in self.subwidgets_all():
            i.config(bg=bg)
        # Modify the balloon label
        self.message.config(wraplength=self.wraplength)

window = tix.Tk()

lbl = tk.Label(window, text="\n".join(["TEXT LABEL"] * 5))
lbl.pack()

b = Balloon(window.winfo_toplevel())
b.bind_widget(lbl, balloonmsg="Context Help Text \nbound to this label widget")

window.mainloop()
