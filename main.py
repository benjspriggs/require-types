"""Usage:
    main.py demo
    main.py convert
"""
from docopt import docopt
from glob import glob
from calmjs.parse import es5
from parsed_module import formatted_module

def parsed(fn: str):
    with open(fn, 'r') as f:
        s = f.readlines()
    return es5('\n'.join(s))

def formatted(fn):
    tree = parsed(fn)
    return formatted_module(tree)

def demo():
    for fn in glob("tests/**/*"):
        print('\n'.join(formatted(fn)))

if __name__ == "__main__":
    arguments = docopt(__doc__)
    
    if arguments["demo"]:
        demo()
    elif arguments["convert"]:
        import sys
        
        lines = sys.stdin.readlines()
        pm = es5('\n'.join(lines))
        print('\n'.join(formatted_module(pm)))
