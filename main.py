from glob import glob
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
Juice = namedtuple('Juice', ['imports', 'statements', 'exports'])

def is_return(s):
    return isinstance(s, asttypes.Return)

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
        statements = [s for s in dependent_code.elements if not is_return(s)]

        rstatement = next(filter(is_return, dependent_code.elements), None)

        yield Juice(imports=zip(import_source.items, imported_names), statements=statements, exports=rstatement)

def j(s):
    for import_statement in s.imports:
        source, name = import_statement
        print("import * as {} = require({})".format(name.value, source.value))

    print('\n'.join([str(statement) for statement in s.statements]))

    # returns, if any
    if s.exports:
        if isinstance(s.exports.expr, asttypes.Identifier):
            # simple export
            print('export default {}'.format(s.exports.expr.value))
        elif isinstance(s.exports.expr, asttypes.FuncExpr):
            # function export
            name = s.exports.expr.identifier
            args = ', '.join([p.value for p in s.exports.expr.parameters])
            body = '\n'.join([str(line) for line in s.exports.expr.elements])
            print('export default function {}({}){{\n{}\n}}'.format(name, args, body))
        elif isinstance(s.exports.expr, asttypes.Object):
            # object export
            props = s.exports.expr.properties
            as_props = ', '.join(['{} as {}'.format(p.left.value, p.right.value) for p in props])
            print('export {{ {} }}'.format(as_props))

def main():
    for fn in glob("tests/*"):
        tree = parsed(fn)
        l = juice(tree)
        for x in l:
            j(x)

if __name__ == "__main__":
    main()
