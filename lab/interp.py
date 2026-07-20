import ast
import code
import operator as op
import numpy as np
from icecream import ic

def evaluator(trace=False):
    def eval(expr, env):
        e = lambda expr: eval(expr, env)
        if isinstance(expr, ast.Module):
            return list(map(e, expr.body))[-1]
        elif isinstance(expr, ast.Constant):
            return expr.value
        elif isinstance(expr, ast.UnaryOp):
            return prim_exprs[type(expr.op)](e(expr.operand))
        elif isinstance(expr, ast.BinOp):
            return prim_exprs[type(expr.op)](e(expr.left), e(expr.right))
        elif isinstance(expr, ast.Expr):
            return e(expr.value)
        elif isinstance(expr, ast.Name):
            return env[expr.id]
        elif isinstance(expr, ast.Assign):
            # does not handle mult assignmnents
            value = e(expr.value)
            env[expr.targets[0].id] = value
            return value
        elif isinstance(expr, ast.If):
            ic(vars(expr))
            test = e(expr.test)
            branch = expr.body if test else expr.orelse
            return [e(b) for b in expr.body][-1]
        elif isinstance(expr, ast.Call):
            f, args = e(expr.func), [e(x) for x in expr.args]
            if callable(f):
                return f(*args)
            ic((f, args))
        elif isinstance(expr, ast.Call):
            f, args = e(expr.func), [e(x) for x in expr.args]
            if callable(f):
                return f(*args)
            ic((f, args))
        elif isinstance(expr, ast.FunctionDef):
            names = [arg.arg for arg in expr.args.args]
            def f(*args):
                body_env = env | dict(zip(names, args))
                try:
                    for e in expr.body:
                        eval(e, body_env)
                    return None
                except Return as exc:
                    return exc.value
            f.__name__ = f.__qualname__ = expr.name
            env[expr.name] = f
            return None
        elif isinstance(expr, ast.Return):
            raise Return(e(expr.value))
        elif isinstance(expr, ast.List):
            return [e(elt) for elt in expr.elts]
        elif isinstance(expr, ast.Dict):
            return {e(k): e(v) for k, v in zip(expr.keys, expr.values)}
        ic(vars(expr))
        raise RuntimeError(f"cannot eval {expr!r}")

    if trace:
        indent = 0
        eval_inner = eval
        def tracer(expr, env):
            nonlocal indent
            msg = f"{' ' * indent}{type(expr).__name__:8} | {unparse(expr)}"
            print(f"{msg} = ...")
            try:
                indent += 1
                result = eval_inner(expr, env)
                print(f"{msg} = {result!r}")
                return result
            finally:
                indent -= 1

        eval = tracer
    return eval

class Return(Exception):
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return f"Return({self.value!r})"

def vectorize(scalar_op, np_op=None):
    np_op = np_op or scalar_op
    def g(*args):
        has_number = any(map(is_number, args))
        has_numeric_sequence = any(map(is_numeric_sequence, args))
        if has_number or has_numeric_sequence:
            args = [np.array(arg) for arg in args]
            return np_op(*args)
        return scalar_op(*args)
    g.__name__ = g.__qualname__ = scalar_op.__name__
    return g

def is_number(arg):
    return isinstance(arg, (int, float))

def is_numeric_sequence(arg):
    return isinstance(arg, np.ndarray) or (isinstance(arg, (tuple, list)) and all(map(is_number, arg)))

prim_exprs = {
    ast.Add: vectorize(op.add),
    ast.Sub: vectorize(op.sub),
    ast.Mult: vectorize(op.mul),
    ast.Div: vectorize(op.truediv),
    ast.USub: vectorize(op.neg),
}

def unparse(expr):
    try:
        return ast.unparse(expr)
    except Exception:
        return repr(expr)

ic(vectorize(op.add)(2, 3))
ic(vectorize(op.add)(2, (3, 5)))
ic(vectorize(op.add)(np.array([2, 5]), 3))
ic(vectorize(op.mul)(7, np.array([11, 13])))
ic(vectorize(op.truediv)(7, np.array([11, 13])))

##################################################

global_env = {
    "tuple": tuple,
    "list": list,
    "dict": dict,
    "set": set,
    "max": max,
    "min": min,
}

env = global_env | {
    "x": 11,
    "f": lambda a, b: a * 2 + b * 3,
}

def run(code: str):
    print("\n###############################")
    ic(code)
    result = None
    try:
        result = evaluator(trace=True)(ast.parse(code), env)
    except Exception as exc:
        result = exc
        print(f"ERROR : {exc!r}")
    ic(env); ic(result)
    print("###############################\n")
    return result

##################################################

run("2 * 3 + 5")
run("x")
run("x * 7")
run("- x")
run("f(x, 7)")
run("""
def g(a, b):
    return min(a, b - 4)
""")
run("g(2, 3)")
run("g(-5, 3)")
run("[2, 3.5, 'a']")
run("{'a': 2}")
run("value = 5")
run('''
if True:
    val = "a"
else:
    val = "b"
val
''')

run("[1, 2] * 3")

# run("return 'Out Of Scope!'")
