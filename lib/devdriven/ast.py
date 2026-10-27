import ast
# import code

def expr_type(source: str) -> str:
    "Determine if code is a stmt for exec() or an expr for eval()."
    tree = None
    try:
        tree = ast.parse(source)
    # pylint: disable-next=bare-except
    except:  # noqa: E722, S110
        pass
    expr = isinstance(tree, ast.Module) and tree.body and tree.body[0]
    return "expr" if isinstance(expr, ast.Expr) else "stmt"

