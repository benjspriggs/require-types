from collections import namedtuple
from calmjs.parse import es5
from calmjs.parse import asttypes

def parsed(fn):
    with open(fn, 'r') as f:
        s = f.readlines()
    return es5('\n'.join(s))

# statement
#   where the identifier == 'define'
#   copy the arguments of define,
#   copy the arguments to the inner function
#   import the statements within
#   and return a pair
Juice = namedtuple('Juice', ['imports', 'statements'])

def juice(tree):
    if not isinstance(tree, asttypes.ES5Program):
        raise Exception("not a program")

    for statement in tree.children():
        if not isinstance(statement, asttypes.ExprStatement):
            continue
        if statement.expr.identifier.value != "define":
            continue
        import_source, dependent_code = statement.expr.args.items
        imported_names = dependent_code.parameters
        statements = dependent_code.elements
        yield Juice(imports=zip(import_source.items, imported_names), statements=statements)

def j(s):
    for import_statement in s.imports:
        source, name = import_statement
        print("import {} = require({})".format(name.value, source.value))
    print('\n'.join([str(statement) for statement in s.statements]))

def main():
    tree = parsed("tests/multiple-define.js")
    l = juice(tree)
    for x in l:
        j(x)

if __name__ == "__main__":
    main()
