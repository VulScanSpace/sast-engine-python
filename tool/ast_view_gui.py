import tkinter as tk
from tkinter import *
from tkinter import ttk


class karl(Frame):
    def __init__(self):
        tk.Frame.__init__(self)
        self.pack()
        self.master.title("Python AST View")

        self.sourceCodeText = Text(self, width=50, height=30, undo=True, autoseparators=False)
        self.sourceCodeText.pack()
        self.sourceCodeText.insert(END, 'C语言中文网，一个有温度的网站')

        # self.sourceCodeText.grid(row=0, column=2, rowspan=2, padx='4px', pady='5px')


def main():
    karl().mainloop()


root = Tk(baseName='baseName', className='className')
frm = ttk.Frame(root, padding=10)
frm.grid()
ttk.Label(frm, text="Hello World!").grid(column=0, row=0)
ttk.Button(frm, text="Quit", command=root.destroy).grid(column=1, row=0)
root.mainloop()

# if __name__ == '__main__':
#     main()
