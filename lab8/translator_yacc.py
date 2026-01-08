"""
YACC/PLY Parser with C Code Generation
Translates Unit Conversion DSL to C
"""

import ply.lex as lex
import ply.yacc as yacc


# ============================================================================
# LEXER
# ============================================================================

class Lexer:
    """Lexer with FA for identifiers and constants"""

    tokens = (
        'IDENTIFIER',
        'NUMBER',
        'UNIT',
        'PLUS',
        'MINUS',
        'MULTIPLY',
        'DIVIDE',
        'ASSIGN',
        'LPAREN',
        'RPAREN',
        'LBRACE',
        'RBRACE',
        'LBRACKET',
        'RBRACKET',
        'COMMA',
        'EQUAL',
        'NOT_EQUAL',
        'GREATER',
        'LESS',
        'GREATER_EQUAL',
        'LESS_EQUAL',
    )

    reserved = {
        'convert': 'CONVERT',
        'to': 'TO',
        'print': 'PRINT',
        'if': 'IF',
        'then': 'THEN',
        'else': 'ELSE',
        'for': 'FOR',
        'in': 'IN',
        'do': 'DO',
    }

    tokens = tokens + tuple(reserved.values())

    units = {
        'ml', 'cl', 'dl', 'l',
        'mm', 'cm', 'dm', 'm', 'dam', 'hm', 'km',
        'ms', 's', 'min', 'hr', 'd', 'wk', 'mo', 'yr',
        'mg', 'cg', 'dg', 'g', 'dag', 'hg', 'kg', 't'
    }

    t_PLUS = r'\+'
    t_MULTIPLY = r'\*'
    t_DIVIDE = r'/'
    t_ASSIGN = r'='
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_LBRACE = r'\{'
    t_RBRACE = r'\}'
    t_LBRACKET = r'\['
    t_RBRACKET = r'\]'
    t_COMMA = r','
    t_EQUAL = r'=='
    t_NOT_EQUAL = r'!='
    t_GREATER_EQUAL = r'>='
    t_LESS_EQUAL = r'<='
    t_GREATER = r'>'
    t_LESS = r'<'
    t_ignore = ' \t'

    def __init__(self):
        self.lexer = None

    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    def t_MINUS(self, t):
        r'-'
        return t

    def t_NUMBER(self, t):
        r'0|[1-9][0-9]*'
        t.value = int(t.value)
        return t

    def t_IDENTIFIER(self, t):
        r'[a-zA-Z][a-zA-Z0-9]*'
        if t.value in self.reserved:
            t.type = self.reserved[t.value]
        elif t.value in self.units:
            t.type = 'UNIT'
        return t

    def t_error(self, t):
        print(f"Illegal character '{t.value[0]}'")
        t.lexer.skip(1)

    def build(self):
        self.lexer = lex.lex(module=self)
        return self.lexer


# ============================================================================
# PARSER WITH C CODE GENERATION
# ============================================================================

class CCodeGenParser:
    """Parser that generates C code"""

    def __init__(self):
        self.lexer = Lexer()
        self.lexer.build()
        self.tokens = self.lexer.tokens
        self.parser = None

        # Code generation state
        self.c_code = []
        self.indent_level = 0
        self.variables = set()
        self.temp_var_counter = 0

        # Unit conversions
        self.conversions = {
            'mg': 0.001, 'cg': 0.01, 'dg': 0.1, 'g': 1,
            'dag': 10, 'hg': 100, 'kg': 1000, 't': 1000000,
            'mm': 0.001, 'cm': 0.01, 'dm': 0.1, 'm': 1,
            'dam': 10, 'hm': 100, 'km': 1000,
            'ms': 0.001, 's': 1, 'min': 60, 'hr': 3600,
            'd': 86400, 'wk': 604800, 'mo': 2592000, 'yr': 31536000,
            'ml': 0.001, 'cl': 0.01, 'dl': 0.1, 'l': 1
        }

    def emit(self, code):
        """Emit C code with indentation"""
        indent = "    " * self.indent_level
        self.c_code.append(indent + code)

    def new_temp(self):
        """Generate temporary variable name"""
        self.temp_var_counter += 1
        return f"_t{self.temp_var_counter}"

    # Grammar rules

    def p_program(self, p):
        '''program : statement_list'''
        p[0] = ('program', p[1])

    def p_statement_list(self, p):
        '''statement_list : statement statement_list
                          | empty'''
        if len(p) == 3:
            p[0] = ('stmt_list', p[1], p[2])
        else:
            p[0] = ('stmt_list', 'epsilon')

    def p_statement(self, p):
        '''statement : assignment_stmt
                     | conversion_stmt
                     | print_stmt
                     | if_stmt
                     | for_stmt'''
        p[0] = p[1]

    def p_assignment_stmt(self, p):
        '''assignment_stmt : IDENTIFIER ASSIGN expression unit_opt'''
        var_name = p[1]
        expr_code, expr_value = p[3]
        unit = p[4]

        # Emit expression code first
        for line in expr_code:
            self.emit(line)

        # Declare variable if first use
        if var_name not in self.variables:
            self.variables.add(var_name)
            self.emit(f"double {var_name};")

        # Apply unit conversion if present
        if unit:
            factor = self.conversions.get(unit, 1)
            self.emit(f"{var_name} = {expr_value} * {factor};")
        else:
            self.emit(f"{var_name} = {expr_value};")

        p[0] = ('assign', var_name)

    def p_conversion_stmt(self, p):
        '''conversion_stmt : CONVERT IDENTIFIER TO UNIT'''
        var_name = p[2]
        target_unit = p[4]

        factor = self.conversions.get(target_unit, 1)
        self.emit(f"// Convert {var_name} to {target_unit}")
        self.emit(f"{var_name} = {var_name} / {factor};")

        p[0] = ('convert', var_name, target_unit)

    def p_print_stmt(self, p):
        '''print_stmt : PRINT expression'''
        expr_code, expr_value = p[2]

        # Emit expression code
        for line in expr_code:
            self.emit(line)

        self.emit(f'printf("%f\\n", {expr_value});')

        p[0] = ('print', expr_value)

    def p_if_stmt(self, p):
        '''if_stmt : IF condition THEN block else_opt'''
        cond_code, cond_expr = p[2]

        # Emit condition code
        for line in cond_code:
            self.emit(line)

        self.emit(f"if ({cond_expr}) {{")
        self.indent_level += 1

        # Process then block (already emitted)

        self.indent_level -= 1

        # Handle else
        if p[5]:
            self.emit("} else {")
            self.indent_level += 1
            # else block already emitted
            self.indent_level -= 1

        self.emit("}")

        p[0] = ('if', cond_expr)

    def p_else_opt(self, p):
        '''else_opt : ELSE block
                    | empty'''
        p[0] = p[1] if len(p) == 3 else None

    def p_for_stmt(self, p):
        '''for_stmt : FOR IDENTIFIER IN list_expr DO block'''
        loop_var = p[2]
        list_code, list_items = p[4]

        # Generate array
        array_name = f"arr_{loop_var}"
        items_str = ", ".join([str(item) for item in list_items])

        self.emit(f"double {array_name}[] = {{{items_str}}};")
        self.emit(f"int {array_name}_size = {len(list_items)};")

        if loop_var not in self.variables:
            self.variables.add(loop_var)

        self.emit(f"for (int _i = 0; _i < {array_name}_size; _i++) {{")
        self.indent_level += 1
        self.emit(f"double {loop_var} = {array_name}[_i];")

        # Block already emitted

        self.indent_level -= 1
        self.emit("}")

        p[0] = ('for', loop_var)

    def p_block(self, p):
        '''block : LBRACE statement_list RBRACE'''
        p[0] = ('block', p[2])

    def p_condition(self, p):
        '''condition : expression comparison_op expression'''
        left_code, left_val = p[1]
        op = p[2]
        right_code, right_val = p[3]

        all_code = left_code + right_code
        cond_expr = f"{left_val} {op} {right_val}"

        p[0] = (all_code, cond_expr)

    def p_comparison_op(self, p):
        '''comparison_op : EQUAL
                         | NOT_EQUAL
                         | GREATER
                         | LESS
                         | GREATER_EQUAL
                         | LESS_EQUAL'''
        op_map = {
            '==': '==', '!=': '!=', '>': '>', '<': '<', '>=': '>=', '<=': '<='
        }
        p[0] = op_map.get(p[1], p[1])

    def p_list_expr(self, p):
        '''list_expr : LBRACKET list_elements RBRACKET'''
        p[0] = ([], p[2])

    def p_list_elements(self, p):
        '''list_elements : expression list_tail
                         | empty'''
        if len(p) == 3 and p[1]:
            expr_code, expr_val = p[1]
            tail = p[2]
            p[0] = [expr_val] + tail
        else:
            p[0] = []

    def p_list_tail(self, p):
        '''list_tail : COMMA expression list_tail
                     | empty'''
        if len(p) == 4:
            expr_code, expr_val = p[2]
            tail = p[3]
            p[0] = [expr_val] + tail
        else:
            p[0] = []

    def p_expression(self, p):
        '''expression : term expression_tail'''
        term_code, term_val = p[1]
        tail_code, tail_val = p[2]

        if tail_val:
            # There's an operation
            temp = self.new_temp()
            all_code = term_code + tail_code + [f"double {temp} = {term_val} {tail_val};"]
            p[0] = (all_code, temp)
        else:
            p[0] = (term_code, term_val)

    def p_expression_tail(self, p):
        '''expression_tail : PLUS term expression_tail
                           | MINUS term expression_tail
                           | empty'''
        if len(p) == 4:
            op = p[1]
            term_code, term_val = p[2]
            tail_code, tail_val = p[3]

            if tail_val:
                combined = f"{op} {term_val} {tail_val}"
            else:
                combined = f"{op} {term_val}"

            p[0] = (term_code + tail_code, combined)
        else:
            p[0] = ([], None)

    def p_term(self, p):
        '''term : factor term_tail'''
        factor_code, factor_val = p[1]
        tail_code, tail_val = p[2]

        if tail_val:
            temp = self.new_temp()
            all_code = factor_code + tail_code + [f"double {temp} = {factor_val} {tail_val};"]
            p[0] = (all_code, temp)
        else:
            p[0] = (factor_code, factor_val)

    def p_term_tail(self, p):
        '''term_tail : MULTIPLY factor term_tail
                     | DIVIDE factor term_tail
                     | empty'''
        if len(p) == 4:
            op = p[1]
            factor_code, factor_val = p[2]
            tail_code, tail_val = p[3]

            if tail_val:
                combined = f"{op} {factor_val} {tail_val}"
            else:
                combined = f"{op} {factor_val}"

            p[0] = (factor_code + tail_code, combined)
        else:
            p[0] = ([], None)

    def p_factor_number(self, p):
        '''factor : NUMBER unit_opt'''
        num = p[1]
        unit = p[2]

        if unit:
            factor = self.conversions.get(unit, 1)
            value = f"({num} * {factor})"
        else:
            value = str(num)

        p[0] = ([], value)

    def p_factor_identifier(self, p):
        '''factor : IDENTIFIER'''
        p[0] = ([], p[1])

    def p_factor_paren(self, p):
        '''factor : LPAREN expression RPAREN'''
        expr_code, expr_val = p[2]
        p[0] = (expr_code, f"({expr_val})")

    def p_unit_opt(self, p):
        '''unit_opt : UNIT
                    | empty'''
        p[0] = p[1] if p[1] else None

    def p_empty(self, p):
        '''empty :'''
        pass

    def p_error(self, p):
        if p:
            print(f"Syntax error at token {p.type} ('{p.value}')")
        else:
            print("Syntax error at EOF")

    def build(self):
        """Build the parser"""
        self.parser = yacc.yacc(module=self)
        return self.parser

    def parse_and_generate(self, source_code):
        """Parse source and generate C code"""
        # Reset state
        self.c_code = []
        self.indent_level = 0
        self.variables = set()
        self.temp_var_counter = 0

        # Generate header
        self.emit("#include <stdio.h>")
        self.emit("#include <stdlib.h>")
        self.emit("")
        self.emit("int main() {")
        self.indent_level += 1

        # Parse
        result = self.parser.parse(source_code, lexer=self.lexer.lexer)

        # Generate footer
        self.emit("return 0;")
        self.indent_level -= 1
        self.emit("}")

        return "\n".join(self.c_code)


# ============================================================================
# MAIN TEST PROGRAM
# ============================================================================

def main():
    """Test YACC parser with C code generation"""

    test_programs = [
        ("simple_assignment", "x = 5 kg\nprint x"),
        ("conversion", "x = 100 kg\nconvert x to g\nprint x"),
        ("arithmetic", "result = 10 + 20 * 3\nprint result"),
        ("if_statement", "x = 15\nif x > 10 then {\n    print x\n}"),
        ("if_else", "x = 5\nif x > 10 then {\n    y = 1\n} else {\n    y = 0\n}\nprint y"),
        ("for_loop", "for i in [1, 2, 3] do {\n    print i\n}"),
    ]

    parser = CCodeGenParser()
    parser.build()

    for test_name, dsl_code in test_programs:
        print("=" * 80)
        print(f"TEST: {test_name}")
        print("=" * 80)
        print("DSL Code:")
        print(dsl_code)
        print("\n" + "-" * 80)

        try:
            c_code = parser.parse_and_generate(dsl_code)

            print("Generated C Code (YACC):")
            print("-" * 80)
            print(c_code)
            print()

            # Save to file
            filename = f"{test_name}_yacc.c"
            with open(filename, 'w') as f:
                f.write(c_code)
            print(f"✓ Saved to {filename}\n")

        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()

        # Reset parser for next test
        parser = CCodeGenParser()
        parser.build()


if __name__ == "__main__":
    main()