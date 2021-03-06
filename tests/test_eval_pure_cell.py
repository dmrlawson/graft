import pytest
from graftlib.env import Env
from graftlib.eval_cell import (
    ArrayValue,
    NativeFunctionValue,
    NoneValue,
    NumberValue,
    StringValue,
    eval_cell,
    eval_cell_list,
)
from graftlib.lex_cell import lex_cell
from graftlib.parse_cell import FunctionCallTree, parse_cell
from graftlib.programenv import ProgramEnv
from graftlib import make_graft_env


# --- Utils ---


def make_env():
    ret = ProgramEnv(Env(), None, None, eval_cell)
    make_graft_env.add_cell_symbols(ret)
    return ret


def evald(inp, env=None):
    if env is None:
        env = make_env()
    return eval_cell_list(parse_cell(lex_cell(inp)), env)


def assert_prog_fails(program, error, env=None):
    with pytest.raises(
        Exception,
        match=error
    ):
        evald(program, env)


# --- Evaluating ---


def test_Evaluating_an_empty_program_gives_none():
    assert evald("") == NoneValue()


def test_Evaluating_a_primitive_returns_itself():
    assert evald("3") == NumberValue(3)
    assert evald("3.1") == NumberValue(3.1)
    assert evald("-3.1") == NumberValue(-3.1)
    assert evald("'foo'") == StringValue("foo")


def test_Arithmetic_expressions_come_out_correct():
    assert evald("3+4") == NumberValue(7)
    assert evald("3-4") == NumberValue(-1)
    assert evald("3*4") == NumberValue(12)
    assert evald("3*-4") == NumberValue(-12)
    assert evald("3/4") == NumberValue(0.75)


def test_Modifying_arithmetic_expressions_come_out_correct():
    assert evald("r=3 r+=4 r") == NumberValue(7)
    assert evald("r=3 r-=4 r") == NumberValue(-1)
    assert evald("r=3 r*=4 r") == NumberValue(12)
    assert evald("r=3 r/=4 r") == NumberValue(0.75)


def test_Modifying_uninitialised_variables_comes_out_correct():
    assert evald("d+=4 d") == NumberValue(4)


def TODO_FAILS_test_Modifying_by_negative_numbers_comes_out_correct():
    assert evald("r=3 r+=-4 r") == NumberValue(-1)
    assert evald("r=3 r*=-4 r") == NumberValue(-12)


def test_Referring_to_an_unknown_symbol_yields_0():
    assert evald("unkn") == NumberValue(0.0)


def TODO_FAILS_test_Can_define_a_value_as_a_negative():
    assert evald("x=-30 x") == NumberValue(-30)


def test_Can_define_a_value_and_retrieve_it():
    assert evald("x=30 x ") == NumberValue(30)
    assert evald("y='foo' y") == StringValue("foo")


def test_Undefined_variables_are_equal_to_0():
    assert evald("foo") == NumberValue(0)


def test_Modifying_a_value_is_allowed():
    assert evald("x=30 x=10 x") == NumberValue(10)


def test_Negating_a_symbol():
    assert evald("x=30 x=10 -x") == NumberValue(-10)


def test_Value_of_an_assignment_is_the_value_assigned():
    assert evald("x=31") == NumberValue(31)


def test_Negative_assignment():
    assert evald("x=-31") == NumberValue(-31)


def test_None_evaluates_to_None():
    assert (
        eval_cell_list([NoneValue()], make_env) ==
        NoneValue()
    )


def test_Calling_a_function_returns_its_last_value():
    assert (
        evald("{10 11}()") ==
        NumberValue(11)
    )


def test_Body_of_a_function_can_use_arg_values():
    assert (
        evald("{:(x,y)x+y}(100,1)") ==
        NumberValue(101)
    )


def test_Can_hold_a_reference_to_a_function_and_call_it():
    assert (
        evald(
            """
            add={:(x,y)x+y}
            add(20,2.2)
            """
        ) ==
        NumberValue(22.2)
    )


# Not true in the mutable version of Cell
# def test_A_symbol_has_different_life_inside_and_outside_a_function():
#     """Define a symbol outside a function, redefine inside,
#        then evaluate outside.  What happened inside the
#        function should not affect the value outside."""
#
#     assert (
#         evald(
#             """
#             foo="bar"
#             {foo=3}()
#             foo
#             """
#         ) ==
#         StringValue("bar")
#     )


def test_A_symbol_within_a_function_has_the_local_value():
    assert (
        evald(
            """
            foo=3
            bar={foo=77 foo}()
            bar
            """
        ) ==
        NumberValue(77)
    )


def test_Native_function_gets_called():
    def native_fn(_env, x, y):
        return NumberValue(x.value + y.value)
    env = make_env()
    env.set("native_fn", NativeFunctionValue(native_fn))
    assert evald("native_fn(2,8)", env) == NumberValue(10)


def test_Wrong_number_of_arguments_to_a_function_is_an_error():
    assert_prog_fails(
        "{}(3)",
        (
            "1 arguments passed to function " +
            r"FunctionDefTree\(params=\[\], body=\[\]\), " +
            "but it requires 0 arguments."
        ),
    )
    assert_prog_fails(
        "x={:(a,b,c)} x(3,2)",
        (
            r"2 arguments passed to function SymbolTree\(value='x'\), " +
            "but it requires 3 arguments."
        ),
    )


def test_Wrong_number_of_arguments_to_a_native_function_is_an_error():
    def native_fn0(_env):
        return NumberValue(12)

    def native_fn3(_env, _x, _y, _z):
        return NumberValue(12)
    env = make_env()
    env.set("native_fn0", NativeFunctionValue(native_fn0))
    env.set("native_fn3", NativeFunctionValue(native_fn3))
    assert_prog_fails(
        "native_fn0(3)",
        (
            "1 arguments passed to function " +
            r"SymbolTree\(value='native_fn0'\), " +
            "but it requires 0 arguments."
        ),
        env
    )
    assert_prog_fails(
        "native_fn3(3,2)",
        (
            "2 arguments passed to function " +
            r"SymbolTree\(value='native_fn3'\), " +
            "but it requires 3 arguments."
        ),
        env
    )


def test_Function_arguments_are_independent():
    assert (
        evald(
            """
            fn={:(x){x}}
            a=fn("a")
            b=fn("b")
            a()
            """
        ) ==
        evald("'a'")
    )
    assert (
        evald(
            """
            fn={:(x){x}}
            a=fn("a")
            b=fn("b")
            b()
            """
        ) ==
        evald("'b'")
    )


def test_Modifying_inside_an_env_modifies_the_outside():
    assert (
        evald(
            """
            fn={:(arg)global1=2 global2+=10 arg=200}
            global1=1
            global2=10
            arg=100
            fn(2000)
            arg+global1+global2
            """
        ) ==
        evald("122")  # globals get changes, arg does not
    )


def test_A_native_function_can_edit_the_environment():
    def mx3(env):
        env.set("x", NumberValue(3))
    env = make_env()
    env.set("make_x_three", NativeFunctionValue(mx3))
    assert (
        evald("x=1 make_x_three() x", env) ==
        NumberValue(3)
    )


def test_A_closure_holds_updateable_values():
    def dumb_set(env, sym, val):
        env.parent().parent().parent().set(sym.value, val)

    def dumb_if_equal(env, val1, val2, then_fn, else_fn):
        if val1 == val2:
            ret = then_fn
        else:
            ret = else_fn
        return eval_cell_list([FunctionCallTree(ret, [])], env)
    env = make_env()
    env.set("dumb_set", NativeFunctionValue(dumb_set))
    env.set("dumb_if_equal", NativeFunctionValue(dumb_if_equal))
    assert (
        evald(
            """
            counter={
                x=0
                {:(meth)
                    dumb_if_equal(
                        meth,
                        "get",
                        {x},
                        {dumb_set("x",x+1)}
                    )
                }
            }()
            counter("inc")
            counter("inc")
            counter("get")
            """,
            env
        ) ==
        NumberValue(2)
    )


def test_Array_literal():
    assert (
        evald("[3,4]") == ArrayValue([NumberValue(3), NumberValue(4)])
    )


def test_Get_from_array():
    assert evald("x=[3,4] Get(x,0)") == NumberValue(3)


def test_Get_from_array_literal():
    assert evald("Get([3,4],1)") == NumberValue(4)


def test_Add_to_array_literal():
    assert (
        evald("Add([3,4],1)") ==
        ArrayValue(
            [
                NumberValue(3),
                NumberValue(4),
                NumberValue(1),
            ]
        )
    )


def test_Length_of_array():
    assert evald("Len([3,4,7,9,300])") == evald("5")


def test_Get_wraps_around():
    assert evald("Get([0,1,2,3,4],-1)") == NumberValue(4)
    assert evald("Get([0,1,2,3,4],-2)") == NumberValue(3)
    assert evald("Get([0,1,2,3,4],5)") == NumberValue(0)
    assert evald("Get([0,1,2,3,4],6.1)") == NumberValue(1)
    assert evald("Get([0,1,2,3,4],11)") == NumberValue(1)


def test_For_is_really_a_map():
    assert (
        evald(
            """
                For(
                    [1,2,3],
                    {:(it) it*2}
                )
            """
        ) ==
        evald("[2,4,6]")
    )


def test_For_calls_function_until_it_returns_endofloop():
    assert (
        evald(
            """
                counter=0
                iter={counter+=1 If(counter>3,{endofloop},{counter})}
                For(
                    iter,
                    {:(it) it*3}
                )
            """
        ) ==
        evald("[3,6,9]")
    )


def test_Range_builtin():
    assert evald("For(Range(3),{:(i)i})") == evald("[0,1,2]")


def test_Not_builtin():
    assert evald("If(    3==3 ,{0},{3})") == evald("0")
    assert evald("If(Not(3==3),{0},{3})") == evald("3")


def test_While_repeatedly_calls_body_and_returns_an_array():
    assert (
        evald(
            """
                vals=[9,3,5]
                i=7
                j=3
                While({i<10},{j-=1 i+=1 Get(vals,j)})
            """
        ) ==
        evald("[5,3,9]")
    )
    assert evald("If(    3==3 ,{0},{3})") == evald("0")
    assert evald("If(Not(3==3),{0},{3})") == evald("3")


def test_Maths_functions_give_correct_answers():
    def r(nv):
        return NumberValue(round(nv.value))
    assert r(evald("Sin(0)")) == evald("0")
    assert r(evald("Sin(90)")) == evald("1")
    assert r(evald("Cos(0)")) == evald("1")
    assert r(evald("Cos(90)")) == evald("0")
    assert r(evald("Tan(0)")) == evald("0")
    assert r(evald("ASin(1)")) == evald("90")
    assert r(evald("ACos(0)")) == evald("90")
    assert r(evald("ATan(0)")) == evald("0")
    assert r(evald("ATan2(1,1)")) == evald("45")
    assert r(evald("Sqrt(16)")) == evald("4")
    assert r(evald("Pow(2,3)")) == evald("8")
    assert r(evald("Hypot(3,4)")) == evald("5")
