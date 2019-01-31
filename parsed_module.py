from collections import namedtuple
from calmjs.parse import asttypes
from utils import flatten, append
from typing import Iterable, Tuple

class Module:
    def __init__(self, imports: Iterable[Tuple[str, str]], statements, exports):
        self.imports = imports
        self.statements = statements
        self.exports = exports

def is_return(s: asttypes.Node) -> bool:
    return isinstance(s, asttypes.Return)

def is_define(s: asttypes.Node) -> bool:
    if not isinstance(s, asttypes.ExprStatement):
        return False
    return isinstance(s, asttypes.ExprStatement) \
            and hasattr(s.expr, 'identifier') \
            and hasattr(s.expr.identifier, 'value') \
            and s.expr.identifier.value == "define"

def module_from_common_js(statement):
    raise Exception("simplified commonjs modules not supported")

def export_from_dependent_code(dependent_code) -> asttypes.Node:
    return next(filter(is_return, dependent_code.elements), None)

def statements_from_dependent_code(dependent_code) -> Iterable[asttypes.Node]:
    return (s for s in dependent_code.elements if not is_return(s) and not is_define(s))

def module_from_statement(statement: asttypes.Node) -> Module:
    if not is_define(statement):
        yield Module(imports=None, statements=[statement], exports=None)
        return

    define_args = statement.expr.args.items

    if len(define_args) == 1:
        """
        Either a CommonJS module or a simple function export.
        ```js
        define(function() {
            ...
        });
        ```
        or
        ```js
        define(function(require, exports, module) {
            ...
        });
        ```
        """
        if isinstance(define_args[0], asttypes.Object):
            yield Module(imports=None,
                    statements=None,
                    exports=define_args[0])
            return

        dependent_code = define_args[0]

        if len(dependent_code.parameters) == 3:
            yield from module_from_common_js(statement)
            return
        else:
            yield Module(imports=None,
                    statements=statements_from_dependent_code(dependent_code),
                    exports=export_from_dependent_code(dependent_code))
            return
    if len(define_args) == 2:
        """
        Function with dependencies.
        ```js
        define([...], function(...args) {
            ...
        });
        ```
        """
        import_source, dependent_code = define_args
    if len(define_args) == 3:
        """
        Explicitly defined module.
        ```js
        define("name/of/module", [...], function(...args) {
            ...
        });
        ```
        """
        _, import_source, dependent_code = define_args

    import_source, dependent_code = define_args
    imported_names = dependent_code.parameters

    imports = zip(import_source.items, imported_names)

    statements = statements_from_dependent_code(dependent_code)

    nested_define_statements = (s for s in dependent_code.elements if is_define(s))

    if nested_define_statements:
        inner_statements = (flatten([module_from_statement(s) for s in nested_define_statements]))
        imports = append(imports, lambda m: m.imports, inner_statements)
        statements = append(statements, lambda m: m.statements, inner_statements)

    rstatement = export_from_dependent_code(dependent_code)

    yield Module(imports=imports,
            statements=statements, 
            exports=rstatement)

def module(tree: asttypes.ES5Program) -> Iterable[Module]:
    if not isinstance(tree, asttypes.ES5Program):
        raise Exception("not a program")

    for statement in tree.children():
        if not isinstance(statement, asttypes.ExprStatement):
            yield Module(imports=None, statements=[statement], exports=None)
        else:
            yield from module_from_statement(statement)

def format_module(s: Module) -> Iterable[str]:
    if s.imports:
        for import_statement in s.imports:
            source, name = import_statement
            yield ("import * as {} from {}".format(name.value, source.value))

    if s.statements:
        yield from ([str(statement) for statement in s.statements])

    # returns, if any
    if s.exports:
        if not hasattr(s.exports, 'expr'):
            """
            ```js
            define({
                color: "black",
                size: "unisize"
            });
            ```
            """
            yield ('export default {}'.format(s.exports))
        elif isinstance(s.exports.expr, asttypes.Identifier):
            """
            ```js
            define(..., function () {
                var name = ...;
                return name;
            });
            ```
            """
            yield ('export default {}'.format(s.exports.expr.value))
        elif isinstance(s.exports.expr, asttypes.FuncExpr):
            """
            ```js
            define(..., function () {
                var name = ...;
                return function () {
                    ...;
                };
            });
            ```
            or:
            ```js
            define(..., function () {
                var name = ...;
                return function NamedFunction() {
                    ...;
                };
            });
            ```
            """
            name = s.exports.expr.identifier
            args = ', '.join(p.value for p in s.exports.expr.parameters)
            body = (str(line) for line in s.exports.expr.elements)
            yield ('export default function {}({}) {{'.format(name, args))
            yield from body
            yield '}'
        elif isinstance(s.exports.expr, asttypes.Object):
            """
            define(..., function () {
                return {
                    ...;
                };
            });
            """
            props = s.exports.expr.properties
            as_props = ', '.join('{} as {}'.format(p.left.value, p.right.value) for p in props)
            yield ('export {{ {} }}'.format(as_props))

def formatted_module(tree: asttypes.ES5Program) -> Iterable[str]:
    return flatten(format_module(m) for m in module(tree))

