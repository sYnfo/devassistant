
# XXX Don't use infix/prefix for symbols you init manualy?
# XXX cut newline from $() ret value
# XXX $() should assign stout AND stderr
# XXX $(cd) should be treated differently?
# XXX Should I put tokenize outside of the interpreter class?

import shlex
import subprocess
from subprocess import Popen


class interpreter(object):
    """
    Interpreter of DevAssistant DSL implemented using Pratt's parser.
    For more info, see:
    * mauke.hopto.org/stuff/papers/p41-pratt.pdf
    * http://javascript.crockford.com/tdop/tdop.html
    * http://effbot.org/zone/simple-top-down-parsing.htm
    """

    def __init__(self, names):
        # A dictionary of variables in the form of {name: value, ...}
        self.names = names

        # A dictionary of symbols in the form of
        # {name of the symbol: its class}
        self.symbol_table = {}

        # Holds the current token
        self.token = None

        # The tokenizer considers all tokens in "$()" to be literal tokens
        self.in_shell = False

    class symbol_base(object):
        id = None
        value = None
        first = second = None

        def nud(self):
            raise SyntaxError("Syntax error ({}).".format(self.id))

        def led(self, left):
            raise SyntaxError("Unknown operator ({}).".format(self.id))

    def symbol(self, id, bp=0):
        """
        Adds symbol 'id' to symbol_table if it does not exist already
        and returns it's symbol class
        """

        try:
            s = self.symbol_table[id]
        except KeyError:
            class s(self.symbol_base):
                pass
            s.id = id
            s.lbp = bp
            self.symbol_table[id] = s
        else:
            s.lbp = max(bp, s.lbp)
        return s

    def advance(self, id=None):
        """
        Advance to next token, optionally check that current token is 'id'
        """

        if id and self.token.id != id:
            raise SyntaxError("Expected {}".format(id))
        self.token = self.next()

    def method(self, symbol_name):
        """
        Adds this method to symbol 'symbol_name'
        """

        s = self.symbol(symbol_name)

        def bind(fn):
            setattr(s, fn.__name__, fn)
        return bind

    def tokenize(self, program):
        self.in_shell = False
        lexer = shlex.shlex(program)
        lexer.wordchars += "$-/\\"
        for tok in lexer:
            if tok in ["and", "or", "not", "defined", "(", ")", "in", "$"]:
                # operators
                symbol = self.symbol_table.get(tok)
                if not symbol:
                    raise SyntaxError("Unknown operator")
                yield symbol()
            elif tok.startswith("$"):
                # names
                symbol = self.symbol_table["(name)"]
                s = symbol()
                s.value = tok
                yield s
            elif tok.startswith('"'):
                # literals
                symbol = self.symbol_table["(literal)"]
                s = symbol()
                s.value = tok.strip('"')
                yield s
            else:
                if not self.in_shell:
                    raise SyntaxError("Unknown token")
                else:
                    # inside shell, everything is a literal
                    symbol = self.symbol_table["(literal)"]
                    s = symbol()
                    s.value = tok
                    yield s
        symbol = self.symbol_table["(end)"]
        yield symbol()

    def expression(self, rbp=0):
        t = self.token
        self.token = self.next()
        left = t.nud()
        while rbp < self.token.lbp:
            t = self.token
            self.token = self.next()
            left = t.led(left)
        return left

    def parse(self, program):
        self.next = self.tokenize(program).next
        self.token = self.next()
        return self.expression()


def evaluate(expression, names):
    interpr = interpreter(names)

    ## Language definition
    # First, all the symbols, along with their binding power
    interpr.symbol("and", 10)
    interpr.symbol("or", 10)
    interpr.symbol("not", 10)
    interpr.symbol("in", 10)
    interpr.symbol("defined", 10)
    interpr.symbol("$", 10)
    interpr.symbol("(name)")
    interpr.symbol("(literal)")
    interpr.symbol("(end)")
    interpr.symbol("(")
    interpr.symbol(")")

    # Specify the behaviour of each symbol
    # nud stands for
    # led stand for
    @interpr.method("(name)")
    def nud(self):
        # XXX Should we return False or exception?
        try:
            return (bool(interpr.names[self.value[1:]]),
                    interpr.names[self.value[1:]])
        except:
            return (False, False)

    @interpr.method("(literal)")
    def nud(self):
        # If there is a known variable in the literal, substitute it for its
        # value
        for v in reversed(sorted(interpr.names.keys())):
            self.value = self.value.replace("$" + v, str(interpr.names[v]))

        return bool(self.value), self.value

    @interpr.method("and")
    def led(self, left):
        right = interpr.expression(10)
        return bool(left[0] and right[0]), left[1] and right[1]

    @interpr.method("or")
    def led(self, left):
        right = interpr.expression(10)
        return bool(left[0] or right[0]), left[1] or right[1]

    @interpr.method("not")
    def nud(self):
        right = interpr.expression(10)
        return bool(not right[0]), not right[1]

    @interpr.method("in")
    def led(self, left):
        result = left[1] in interpr.expression(10)[1]
        return bool(result), left[1]

    @interpr.method("defined")
    def nud(self):
        if interpr.token.id != "(name)":
            raise SyntaxError("Expected a name")
        name = interpr.token.value[1:]
        interpr.advance()
        result = name in interpr.names
        return bool(result), "$" + name

    @interpr.method("$")
    def nud(self):
        interpr.in_shell = True
        interpr.advance("(")
        self.first = []
        if interpr.token.id != ")":
            while 1:
                if interpr.token.id == ")":
                    break
                # the var nahrazeni must happe nhere
                self.first.append(interpr.token.value)
                interpr.advance()
        command = " ".join(self.first)
        for v in reversed(sorted(interpr.names.keys())):
            command = command.replace("$" + v, str(interpr.names[v]))
        command = "pwd; " + command
        p = Popen(command,
                  stdout=subprocess.PIPE,
                  stderr=subprocess.STDOUT,
                  shell=True)
        output = p.communicate()[0]
        output = output.rstrip()
        output = output.split('\n')[1:]
        output = '\n'.join(output)
        # Dont forget to check the return code
        interpr.advance(")")
        interpr.in_shell = False
        return p.returncode == 0, output

    @interpr.method("(")
    def nud(self):
        self.first = []
        if interpr.token.id != ")":
            while 1:
                if interpr.token.id == ")":
                    break
                self.first.append(interpr.expression())
        interpr.advance(")")
        return bool(self.first[0][0]), self.first[0][1]

    # With that done, evaluate the expression
    return interpr.parse(expression)

if __name__ == "__main__":
    print """
    Set variables:
        $true       :   True
        $false      :   False
        $empty      :   ""
        $nonempty   :   "test"

    Available operators and stuff:
        $foo, defined $foo, and, or, not, (), $()

    Grammar is aprox.:
        TOKEN:  STR
        EXP:    not EXP
            |   EXP and EXP
            |   EXP or EXP
            |   $STR
            |   defined STR
    """
    names = {"true": True, "false": False, "nonempty": "foo", "empty": ""}
    while 1:
        try:
            print(repr(evaluate(raw_input(">>> "), names)))
        except KeyboardInterrupt:
            raise
