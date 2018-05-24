import inspect
from typing import List
import attr

from graftlib.parse2 import (
    AssignmentTree,
    FunctionCallTree,
    FunctionDefTree,
    NumberTree,
    OperationTree,
    StringTree,
    SymbolTree,
)

from graftlib.env import Env


@attr.s
class NativeFunctionValue:
    py_fn: float = attr.ib()


@attr.s
class NoneValue:
    pass


@attr.s
class NumberValue:
    value: float = attr.ib()


@attr.s
class StringValue:
    value: str = attr.ib()


@attr.s
class UserFunctionValue:
    params: List = attr.ib()
    body: List = attr.ib()
    env: Env = attr.ib()


def _operation(expr, env):
    arg1 = eval_expr(expr.left, env)
    arg2 = eval_expr(expr.right, env)
    if expr.operation == "+":
        return NumberValue(arg1.value + arg2.value)
    elif expr.operation == "-":
        return NumberValue(arg1.value - arg2.value)
    elif expr.operation == "*":
        return NumberValue(arg1.value * arg2.value)
    elif expr.operation == "/":
        return NumberValue(arg1.value / arg2.value)
    else:
        raise Exception("Unknown operation: " + expr.operation)


def fail_if_wrong_number_of_args(fn_name, params, args):
    if len(params) != len(args):
        raise Exception((
            "%d arguments passed to function %s, but it " +
            "requires %d arguments."
        ) % (len(args), fn_name, len(params)))


def _function_call(expr, env):
    fn = eval_expr(expr.fn, env)
    args = list((eval_expr(a, env) for a in expr.args))
    typ = type(fn)
    if typ == UserFunctionValue:
        fail_if_wrong_number_of_args(expr.fn, fn.params, args)
        new_env = Env(fn.env)
        for p, a in zip(fn.params, args):
            new_env.set(p.value, a)
        return eval_list(fn.body, new_env)
    elif typ == NativeFunctionValue:
        params = inspect.getargspec(fn.py_fn).args
        fail_if_wrong_number_of_args(expr.fn, params[1:], args)
        return fn.py_fn(env, *args)
    else:
        raise Exception(
            "Attempted to call something that is not a function: %s" %
            str(fn)
        )


def eval_expr(expr, env):
    typ = type(expr)
    if typ == NumberTree:
        return NumberValue(float(expr.value))
    elif typ == StringTree:
        return StringValue(expr.value)
    elif typ == NoneValue:
        return expr
    elif typ == OperationTree:
        return _operation(expr, env)
    elif typ == SymbolTree:
        ret = env.get(expr.value)
        if ret is None:
            raise Exception("Unknown symbol '%s'." % expr.value)
        else:
            return ret
    elif typ == AssignmentTree:
        var_name = expr.symbol.value
        if var_name in env.items:
            raise Exception("Not allowed to re-assign symbol '%s'." % var_name)
        val = eval_expr(expr.value, env)
        env.set(var_name, val)
        return val
    elif typ == FunctionCallTree:
        return _function_call(expr, env)
    elif typ == FunctionDefTree:
        return UserFunctionValue(expr.params, expr.body, Env(env))
    elif typ == UserFunctionValue:
        return expr
    else:
        raise Exception("Unknown expression type: " + str(expr))


def eval_iter(exprs, env):
    for expr in exprs:
        yield eval_expr(expr, env)


def eval_list(exprs, env):
    ret = NoneValue()
    for expr in eval_iter(exprs, env):
        ret = expr
    return ret
