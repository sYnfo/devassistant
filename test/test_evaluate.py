import pytest
from devassistant.yaml_evaluate import evaluate

# XXX Also test for things that should fail

class TestEvaluate(object):
    def setup_method(self, method):
        self.names = {"true": True,
                 "false": False,
                 "nonempty": "foo",
                 "nonempty2": "bar",
                 "empty": ""}

    def test_and(self):
        # XXX or should this be (True, "") or (True, "True")
        assert evaluate("$true and $true", self.names) == (True, True)
        assert evaluate("$true and $false", self.names) == (False, False)
        assert evaluate("$false and $true", self.names) == (False, False)
        assert evaluate("$false and $false", self.names) == (False, False)

        assert evaluate("$nonempty and $nonempty2", self.names) == (True, "bar")
        assert evaluate("$nonempty2 and $nonempty", self.names) == (True, "foo")

        assert evaluate("$nonempty and $empty", self.names) == (False, "")
        assert evaluate("$empty and $nonempty", self.names) == (False, "")

        assert evaluate("$nonempty and $true", self.names) == (True, True)
        assert evaluate("$true and $nonempty", self.names) == (True, "foo")

        assert evaluate("$empty and $true", self.names) == (False, "")
        assert evaluate("$true and $empty", self.names) == (False, "")

        assert evaluate("$empty and $empty", self.names) == (False, "")

        assert evaluate("$true and $nonempty and $nonempty2", self.names) == (True, "bar")
        assert evaluate("$true and $nonempty and $empty", self.names) == (False, "")

    def test_or(self):
        assert evaluate("$true or $true", self.names) == (True, True)
        assert evaluate("$true or $false", self.names) == (True, True)
        assert evaluate("$false or $true", self.names) == (True, True)
        assert evaluate("$false or $false", self.names) == (False, False)

        assert evaluate("$nonempty or $nonempty2", self.names) == (True, "foo")
        assert evaluate("$nonempty2 or $nonempty", self.names) == (True, "bar")

        assert evaluate("$nonempty or $empty", self.names) == (True, "foo")
        assert evaluate("$empty or $nonempty", self.names) == (True, "foo")

        assert evaluate("$nonempty or $true", self.names) == (True, "foo")
        assert evaluate("$true or $nonempty", self.names) == (True, True)

        assert evaluate("$empty or $true", self.names) == (True, True)
        assert evaluate("$true or $empty", self.names) == (True, True)

        assert evaluate("$empty or $empty", self.names) == (False, "")

        assert evaluate("$true or $nonempty or $nonempty2", self.names) == (True, True)
        assert evaluate("$false or $nonempty or $empty", self.names) == (True, "foo")

    def test_not(self):
        assert evaluate("not $true", self.names) == (False, False)
        assert evaluate("not $false", self.names) == (True, True)
        assert evaluate("not $nonempty", self.names) == (False, False)
        assert evaluate("not $empty", self.names) == (True, True)

    def test_in(self):
        assert evaluate('$nonempty in "foobar"', self.names) == (True, "foo")
        assert evaluate('$nonempty2 in "foobar"', self.names) == (True, "bar")
        assert evaluate('$empty in "foobar"', self.names) == (True, "")
        assert evaluate('$nonempty in "FOOBAR"', self.names) == (False, "foo")

    def test_defined(self):
        assert evaluate("defined $nonempty", self.names) == (True, "$nonempty")
        assert evaluate("defined $empty", self.names) == (True, "$empty")
        assert evaluate("defined $notdefined", self.names) == (False, "$notdefined")

    def test_variable(self):
        assert evaluate("$true", self.names) == (True, True)
        assert evaluate("$false", self.names) == (False, False)
        assert evaluate("$nonempty", self.names) == (True, "foo")
        assert evaluate("$empty", self.names) == (False, "")

    def test_shell(self):
        # Also test for if it stays cd'd and if the return code is handled
        # right
        assert evaluate("$(echo foobar)", self.names) == (True, "foobar")
        assert evaluate("$(test -d /thisshouldntexist)", self.names) == (False, '')
        assert evaluate("$(false)", self.names) == (False, '')
        assert evaluate("$(true)", self.names) == (True, '')

    def test_literal(self):
        assert evaluate('"foobar"', self.names) == (True, "foobar")
        assert evaluate('""', self.names) == (False, "")

    def test_parentheses(self):
        pass

    def test_variable_substitution(self):
        assert evaluate('"$nonempty"', self.names) == (True, "foo")
        assert evaluate('"$empty"', self.names) == (False, "")
        # XXX Is this right? Shouldn't it evaluet to a different string?
        assert evaluate('"$true"', self.names) == (True, "True")

    def test_complex_expression(self):
        assert evaluate('defined $empty or $empty and \
                         $(echo -e foo bar "and also baz") or "google"',
                        self.names) == (True, 'foo bar and also baz')

    def test_precedence(self):
        pass
