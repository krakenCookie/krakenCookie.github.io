# Created by Zachary Burchill, 2019
# Feel free to use/modify however you want, but be nice and
#   please give me credit/attribution.
#
# Put this file in your jupyter directory and load it in the first cell with:
#   %load_ext zachmagic
# After that, you can use %beep, %%beep, %time_beep, %%time_beep, %hide_all, 
#   %show_all, %keep_input and %%keep_input in the cells.

from IPython.core.magic import Magics, magics_class, line_magic, cell_magic, line_cell_magic
from IPython.utils.capture import capture_output
from IPython.display import Audio, Code
from IPython.core.display import display, HTML

@magics_class
class MyMagics(Magics):

    # `@line_cell_magic` means that you can either use `%beep` for a single line 
    #   (which would be a little weird, tbh) or `%%beep` for a whole cell
    @line_cell_magic
    def beep(self, line, cell=None):
        ''' 
        Will play a sound when the code of a cell is done running.
        To use, you must have a file called `beep.wav` in your Jupyter directory to play.
        '''
        # If there isn't any `cell` (ie its a single line), execute the line
        exec_val = line if cell is None else cell
        
        # Run the code in the cell, but catch the output so you can display it at the end
        with capture_output(True, False, True) as io:
            self.shell.run_cell(exec_val)
        # Run this code like it was coming from the cell, which will add an audio HTML element
        self.shell.run_cell("""from IPython.display import Audio; Audio("beep.wav", autoplay=True)""")
        # But hide the HTML audio player so all you notice is the beep
        display(HTML('''<style> audio { display: none; } </style>'''))
        # Now show whatever the result of the code in the cell would be
        io.show()
        
    @cell_magic
    def time_beep(self, line, cell):
        '''
        Literally just combines %%time and %%beep
        '''
        exec_val = line if cell is None else cell
        # Just add some magic to the cell and run it again!
        self.shell.run_cell("%%time\n%%beep\n{}".format(exec_val))

    @line_magic
    def hide_all(self, line, cell=None):
        '''
        Hides all code inputs except for those cells with %%keep_input
        '''
        # Hide all the cell inputs (i.e., `<div class='input'>`) with CSS, 
        #   but make divs with the custom class `zach_show` visible 
        #   (See `keep_input()`)
        display(HTML('''<style> div.input { display: none; }  div.zach_show { display: block; }</style>'''))
        # Add this line so you know which cell to delete to stop hiding the inputs
        print("Jupyter inputs set to hide via this cell")
    
    # Technically this function probably will never be used, but it
    #   was so easy to write, why not?
    @line_magic
    def show_all(self, line, cell=None):
      '''
      Makes the input to all cells visible with `display: flex`.
      '''
        display(HTML('''<style> div.input { display: flex; }; div.zach_show { display: none; }</style>'''))
        print("Jupyter inputs set to display via this cell")
    
    # This is my equivalent of `echo = TRUE`
    @line_cell_magic
    def keep_input(self, line, cell=None):
        '''
        Keeps the input to the cell visible even when %hide_all is used.
        '''
        from random import choice
        from string import ascii_uppercase, digits
        exec_val = line if cell is None else cell
        
        # By default the syntax highlighting we want to use is for Python
        lang = "python3"
        # However, if this chunk is R code, we can highlight it according to R's syntax
        if exec_val[0:3] == "%%R" or exec_val[0:2] == "%R":
            lang = "rconsole"
            
        # Hack #1: force the HTML source code we'd display if we were using `Code` normally
        code_to_display = Code(exec_val, language=lang)._repr_html_()
        
        # Hack #2: edit the `Code` HTML, adding a custom class 'zach_show' to the <div>
        #   element that will display the code, and generate a random unique class name 
        #   so the styles we add only apply to the output of this cell
        rclass = ''.join(choice(ascii_uppercase + digits) for _ in range(10))
        code_to_display = code_to_display.replace('<div class="highlight', 
                                                  '<div class="zach_show {} highlight'.format(rclass))
        # Now make the custom stylings from `Code` point to the unique div class rather than being general
        code_to_display = code_to_display.replace('.output_html', 
                                                  '.{}'.format(rclass))

        with capture_output(True, False, True) as io:
            self.shell.run_cell(exec_val)
        # Display the code (it will be hidden if div.zach_show has `display:none`)
        display(HTML(code_to_display))
        io.show()
        
# This needs to be in the file so Jupyter registers the magics when it's loaded
def load_ipython_extension(ipython):
    ipython.register_magics(MyMagics)
    
# This will essentially set the default for our custom class as hidden.
#   When we hide the rest of the inputs, we make the fake input visible.
display(HTML("<style>div.zach_show { display: none; }</style>"))