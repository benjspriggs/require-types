from glob import glob
from collections import namedtuple
from calmjs.parse import es5, asttypes
from utils import flatten, append

def parsed(fn: str):
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

def is_define(s):
    if not isinstance(s, asttypes.ExprStatement):
        return False
    return isinstance(s, asttypes.ExprStatement) \
            and hasattr(s.expr, 'identifier') \
            and hasattr(s.expr.identifier, 'value') \
            and s.expr.identifier.value == "define"

def juice_from_statement(statement):
    import_source, dependent_code = statement.expr.args.items
    imported_names = dependent_code.parameters

    imports = zip(import_source.items, imported_names)

    statements = [s for s in dependent_code.elements if not is_return(s) and not is_define(s)]

    nested_define_statements = [s for s in dependent_code.elements if is_define(s)]

    if nested_define_statements:
        inner_statements = list(flatten([juice_from_statement(s) for s in nested_define_statements]))
        imports = append(imports, lambda j: j.imports, inner_statements)
        statements = append(statements, lambda j: j.statements, inner_statements)

    rstatement = next(filter(is_return, dependent_code.elements), None)

    yield Juice(imports=imports,
            statements=statements, 
            exports=rstatement)

def juice(tree):
    if not isinstance(tree, asttypes.ES5Program):
        raise Exception("not a program")

    for statement in tree.children():
        if not isinstance(statement, asttypes.ExprStatement):
            yield Juice(imports=None, statements=[statement], exports=None)
        else:
            yield from juice_from_statement(statement)

def format_juice(s):
    if s.imports:
        for import_statement in s.imports:
            source, name = import_statement
            yield ("import * as {} = require({})".format(name.value, source.value))

    if s.statements:
        yield from ([str(statement) for statement in s.statements])

    # returns, if any
    if s.exports:
        if isinstance(s.exports.expr, asttypes.Identifier):
            # simple export
            yield ('export default {}'.format(s.exports.expr.value))
        elif isinstance(s.exports.expr, asttypes.FuncExpr):
            # function export
            name = s.exports.expr.identifier
            args = ', '.join([p.value for p in s.exports.expr.parameters])
            body = [str(line) for line in s.exports.expr.elements]
            yield ('export default function {}({}) {{'.format(name, args))
            yield from body
            yield '}'
        elif isinstance(s.exports.expr, asttypes.Object):
            # object export
            props = s.exports.expr.properties
            as_props = ', '.join(['{} as {}'.format(p.left.value, p.right.value) for p in props])
            yield ('export {{ {} }}'.format(as_props))

def formatted(fn):
    tree = parsed(fn)
    return flatten([format_juice(j) for j in juice(tree)])

def main():
    for fn in glob("tests/*"):
        print(list(formatted(fn)))

if __name__ == "__main__":
    main()
