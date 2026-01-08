"""
Lexer and Parser for Unit Conversion Language
Uses PLY (Python Lex-Yacc)
"""

import ply.lex as lex
import ply.yacc as yacc


# ============================================================================
# LEXER (Scanner with FA for identifiers and constants)
# ============================================================================

class Lexer:
    """Lexer with integrated FA for identifiers and constants"""

    # Token list
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

    # Reserved keywords
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

    # Add reserved words to tokens
    tokens = tokens + tuple(reserved.values())

    # Units
    units = {
        'ml', 'cl', 'dl', 'l',  # fluid
        'mm', 'cm', 'dm', 'm', 'dam', 'hm', 'km',  # distance
        'ms', 's', 'min', 'hr', 'd', 'wk', 'mo', 'yr',  # time
        'mg', 'cg', 'dg', 'g', 'dag', 'hg', 'kg', 't'  # weight
    }

    # Simple tokens
    t_PLUS = r'\+'
    t_MINUS = r'-'
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

    # Comparison operators (order matters - longer matches first)
    t_EQUAL = r'=='
    t_NOT_EQUAL = r'!='
    t_GREATER_EQUAL = r'>='
    t_LESS_EQUAL = r'<='
    t_GREATER = r'>'
    t_LESS = r'<'

    # Ignored characters (whitespace)
    t_ignore = ' \t'

    def __init__(self):
        self.lexer = None

    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    def t_NUMBER(self, t):
        # match integers or decimals with optional leading minus
        r'-?(\d+(\.\d+)?)'
        # We accept numbers like: 0, -10, 3.14, -0.5, etc.
        # Convert to int if no decimal part, else float
        sv = t.value
        if '.' in sv:
            try:
                t.value = float(sv)
            except ValueError:
                print(f"Illegal number: {sv}")
                t.lexer.skip(1)
                return
        else:
            try:
                t.value = int(sv)
            except ValueError:
                print(f"Illegal number: {sv}")
                t.lexer.skip(1)
                return
        return t

    def t_IDENTIFIER(self, t):
        r'[a-zA-Z][a-zA-Z0-9]*'
        # Check if it's a reserved keyword
        if t.value in self.reserved:
            t.type = self.reserved[t.value]
            return t
        # Check if it's a unit
        if t.value in self.units:
            t.type = 'UNIT'
            return t
        # Otherwise it's an identifier
        return t

    def t_error(self, t):
        print(f"Illegal character '{t.value[0]}' at line {t.lineno}")
        t.lexer.skip(1)

    def build(self):
        """Build the lexer"""
        self.lexer = lex.lex(module=self)
        return self.lexer


# ============================================================================
# PARSER (Syntactical Analysis)
# ============================================================================

class Parser:
    """Parser for Unit Conversion Language"""

    def __init__(self):
        self.lexer = Lexer()
        self.lexer.build()
        self.tokens = self.lexer.tokens
        self.parser = None
        self.productions = []  # Store derivation steps

    # Grammar Rules with Productions

    def p_program(self, p):
        '''program : statement_list'''
        p[0] = ('program', p[1])
        self.productions.append("program -> statement_list")

    def p_statement_list(self, p):
        '''statement_list : statement statement_list
                          | empty'''
        if len(p) == 3:
            p[0] = ('statement_list', p[1], p[2])
            self.productions.append("statement_list -> statement statement_list")
        else:
            p[0] = ('statement_list', 'epsilon')
            self.productions.append("statement_list -> epsilon")

    def p_statement(self, p):
        '''statement : assignment_stmt
                     | conversion_stmt
                     | print_stmt
                     | if_stmt
                     | for_stmt'''
        p[0] = ('statement', p[1])
        # safe: p.slice[1].type exists for nonterminals like assignment_stmt etc.
        self.productions.append(f"statement -> {p.slice[1].type.lower()}")

    def p_assignment_stmt(self, p):
        '''assignment_stmt : IDENTIFIER ASSIGN expression unit_opt'''
        p[0] = ('assignment', p[1], p[3], p[4])
        self.productions.append("assignment_stmt -> IDENTIFIER = expression unit_opt")

    def p_conversion_stmt(self, p):
        '''conversion_stmt : CONVERT IDENTIFIER TO UNIT'''
        p[0] = ('convert', p[2], p[4])
        self.productions.append("conversion_stmt -> CONVERT IDENTIFIER TO UNIT")

    def p_print_stmt(self, p):
        '''print_stmt : PRINT expression'''
        p[0] = ('print', p[2])
        self.productions.append("print_stmt -> PRINT expression")

    def p_if_stmt(self, p):
        '''if_stmt : IF condition THEN block else_opt'''
        p[0] = ('if', p[2], p[4], p[5])
        self.productions.append("if_stmt -> IF condition THEN block else_opt")

    def p_else_opt(self, p):
        '''else_opt : ELSE block
                    | empty'''
        if len(p) == 3:
            p[0] = ('else', p[2])
            self.productions.append("else_opt -> ELSE block")
        else:
            p[0] = ('else', 'epsilon')
            self.productions.append("else_opt -> epsilon")

    def p_for_stmt(self, p):
        '''for_stmt : FOR IDENTIFIER IN list_expr DO block'''
        p[0] = ('for', p[2], p[4], p[6])
        self.productions.append("for_stmt -> FOR IDENTIFIER IN list_expr DO block")

    def p_block(self, p):
        '''block : LBRACE statement_list RBRACE'''
        p[0] = ('block', p[2])
        self.productions.append("block -> { statement_list }")

    def p_condition(self, p):
        '''condition : expression comparison_op expression'''
        p[0] = ('condition', p[1], p[2], p[3])
        self.productions.append("condition -> expression comparison_op expression")

    def p_comparison_op(self, p):
        '''comparison_op : EQUAL
                         | NOT_EQUAL
                         | GREATER
                         | LESS
                         | GREATER_EQUAL
                         | LESS_EQUAL'''
        p[0] = p[1]
        self.productions.append(f"comparison_op -> {p[1]}")

    def p_list_expr(self, p):
        '''list_expr : LBRACKET list_elements RBRACKET'''
        p[0] = ('list', p[2])
        self.productions.append("list_expr -> [ list_elements ]")

    def p_list_elements(self, p):
        '''list_elements : expression list_tail
                         | empty'''
        if len(p) == 3:
            p[0] = ('list_elements', p[1], p[2])
            self.productions.append("list_elements -> expression list_tail")
        else:
            p[0] = ('list_elements', 'epsilon')
            self.productions.append("list_elements -> epsilon")

    def p_list_tail(self, p):
        '''list_tail : COMMA expression list_tail
                     | empty'''
        if len(p) == 4:
            p[0] = ('list_tail', p[2], p[3])
            self.productions.append("list_tail -> , expression list_tail")
        else:
            p[0] = ('list_tail', 'epsilon')
            self.productions.append("list_tail -> epsilon")

    def p_expression(self, p):
        '''expression : term expression_tail'''
        p[0] = ('expression', p[1], p[2])
        self.productions.append("expression -> term expression_tail")

    def p_expression_tail(self, p):
        '''expression_tail : PLUS term expression_tail
                           | MINUS term expression_tail
                           | empty'''
        if len(p) == 4:
            p[0] = ('expression_tail', p[1], p[2], p[3])
            self.productions.append(f"expression_tail -> {p[1]} term expression_tail")
        else:
            p[0] = ('expression_tail', 'epsilon')
            self.productions.append("expression_tail -> epsilon")

    def p_term(self, p):
        '''term : factor term_tail'''
        p[0] = ('term', p[1], p[2])
        self.productions.append("term -> factor term_tail")

    def p_term_tail(self, p):
        '''term_tail : MULTIPLY factor term_tail
                     | DIVIDE factor term_tail
                     | empty'''
        if len(p) == 4:
            p[0] = ('term_tail', p[1], p[2], p[3])
            self.productions.append(f"term_tail -> {p[1]} factor term_tail")
        else:
            p[0] = ('term_tail', 'epsilon')
            self.productions.append("term_tail -> epsilon")

    def p_factor(self, p):
        '''factor : NUMBER unit_opt
                  | IDENTIFIER
                  | LPAREN expression RPAREN'''
        # Handle three cases explicitly by length
        if len(p) == 3:
            # NUMBER unit_opt  (unit_opt could be None)
            p[0] = ('factor', p[1], p[2])
            self.productions.append("factor -> NUMBER unit_opt")
        elif len(p) == 2:
            # IDENTIFIER
            p[0] = ('factor', p[1])
            self.productions.append("factor -> IDENTIFIER")
        else:
            # Parenthesized expression: LPAREN expression RPAREN
            p[0] = ('factor', p[2])
            self.productions.append("factor -> ( expression )")

    def p_unit_opt(self, p):
        '''unit_opt : UNIT
                    | empty'''
        if len(p) == 2 and p[1] is not None:
            p[0] = p[1]
            self.productions.append("unit_opt -> UNIT")
        else:
            p[0] = None
            self.productions.append("unit_opt -> epsilon")

    def p_empty(self, p):
        '''empty :'''
        pass

    def p_error(self, p):
        if p:
            print(f"Syntax error at token {p.type} ('{p.value}') at line {p.lineno}")
        else:
            print("Syntax error at EOF")

    def build(self):
        """Build the parser"""
        self.parser = yacc.yacc(module=self)
        return self.parser

    def parse(self, input_string):
        """Parse input string and return parse tree + productions"""
        self.productions = []
        result = self.parser.parse(input_string, lexer=self.lexer.lexer)
        return result, self.productions


# ============================================================================
# MAIN PROGRAM
# ============================================================================

def print_parse_tree(tree, indent=0):
    """Pretty print the parse tree"""
    if tree is None:
        return

    if isinstance(tree, tuple):
        print("  " * indent + str(tree[0]))
        for child in tree[1:]:
            print_parse_tree(child, indent + 1)
    else:
        print("  " * indent + str(tree))


def main():
    """Test the integrated scanner and parser"""

    # Test programs
    test_programs = [
        # Test 1: Simple assignment
        ("Simple Assignment", """x = 5 kg"""),

        # Test 2: Conversion
        ("Conversion Statement", """convert distance to km"""),

        # Test 3: Print statement
        ("Print Statement", """print x"""),

        # Test 4: Arithmetic expression
        ("Arithmetic Expression", """result = 10 + 20 * 3"""),

        # Test 5: If statement
        ("If Statement", """if x > 10 then {
    print x
}"""),

        # Test 6: If-else statement
        ("If-Else Statement", """if a == b then {
    print a
} else {
    print b
}"""),

        # Test 7: For loop
        ("For Loop", """for i in [1, 2, 3] do {
    print i
}"""),

        # Test 8: Complex program
        ("Complex Program", """x = 100 kg
convert x to g
if x > 50 then {
    print x
}"""),

        # Test 9: Parenthesized expression
        ("Parenthesized Expression", """result = (a + b) * c"""),
    ]

    parser = Parser()
    parser.build()

    for name, program in test_programs:
        print("=" * 80)
        print(f"TEST: {name}")
        print("=" * 80)
        print("Input Program:")
        print(program)
        print("\n" + "-" * 80)

        try:
            parse_tree, productions = parser.parse(program)

            print("Productions Used (Derivation):")
            print("-" * 80)
            for i, prod in enumerate(productions, 1):
                print(f"{i}. {prod}")

            print("\n" + "-" * 80)
            print("Parse Tree:")
            print("-" * 80)
            print_parse_tree(parse_tree)
            print()

        except Exception as e:
            print(f"Error: {e}")
            print()


if __name__ == "__main__":
    main()
