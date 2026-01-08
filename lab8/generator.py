"""
C Code Generator for Unit Conversion Language
Translates DSL source code to executable C code
"""

import re
from collections import defaultdict


# ============================================================================
# SCANNER (Reuse from previous labs)
# ============================================================================

class Token:
    def __init__(self, token_type, value, position):
        self.type = token_type
        self.value = value
        self.position = position

    def __repr__(self):
        return f"({self.type}, {self.value})"


class Scanner:
    """Scanner with FA for identifiers and constants"""

    def __init__(self):
        self.keywords = {
            'convert', 'to', 'print', 'if', 'then', 'else', 'for', 'in', 'do'
        }
        self.units = {
            'ml', 'cl', 'dl', 'l',
            'mm', 'cm', 'dm', 'm', 'dam', 'hm', 'km',
            'ms', 's', 'min', 'hr', 'd', 'wk', 'mo', 'yr',
            'mg', 'cg', 'dg', 'g', 'dag', 'hg', 'kg', 't'
        }

        self.patterns = [
            ('NUMBER', r'-?\d+'),
            ('IDENTIFIER', r'[a-zA-Z][a-zA-Z0-9]*'),
            ('EQ', r'=='),
            ('NE', r'!='),
            ('GE', r'>='),
            ('LE', r'<='),
            ('GT', r'>'),
            ('LT', r'<'),
            ('ASSIGN', r'='),
            ('PLUS', r'\+'),
            ('MINUS', r'-'),
            ('MULTIPLY', r'\*'),
            ('DIVIDE', r'/'),
            ('LPAREN', r'\('),
            ('RPAREN', r'\)'),
            ('LBRACE', r'\{'),
            ('RBRACE', r'\}'),
            ('LBRACKET', r'\['),
            ('RBRACKET', r'\]'),
            ('COMMA', r','),
            ('WHITESPACE', r'\s+'),
        ]

    def scan(self, source_code):
        """Scan source and return PIF"""
        pif = []
        position = 0

        while position < len(source_code):
            matched = False

            for token_type, pattern in self.patterns:
                regex = re.compile(pattern)
                match = regex.match(source_code, position)

                if match:
                    value = match.group(0)

                    if token_type == 'WHITESPACE':
                        position = match.end()
                        matched = True
                        break

                    if token_type == 'IDENTIFIER':
                        if value in self.keywords:
                            token_type = value.upper()
                        elif value in self.units:
                            token_type = 'UNIT'

                    pif.append(Token(token_type, value, position))
                    position = match.end()
                    matched = True
                    break

            if not matched:
                raise Exception(f"Illegal character at position {position}: '{source_code[position]}'")

        return pif


# ============================================================================
# SIMPLE PARSER (for C code generation)
# ============================================================================

class SimpleParser:
    """Simple recursive descent parser for code generation"""

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.variables = set()
        self.unit_conversions = {
            # Weight conversions to grams
            'mg': 0.001, 'cg': 0.01, 'dg': 0.1, 'g': 1,
            'dag': 10, 'hg': 100, 'kg': 1000, 't': 1000000,
            # Distance conversions to meters
            'mm': 0.001, 'cm': 0.01, 'dm': 0.1, 'm': 1,
            'dam': 10, 'hm': 100, 'km': 1000,
            # Time conversions to seconds
            'ms': 0.001, 's': 1, 'min': 60, 'hr': 3600,
            'd': 86400, 'wk': 604800, 'mo': 2592000, 'yr': 31536000,
            # Fluid conversions to liters
            'ml': 0.001, 'cl': 0.01, 'dl': 0.1, 'l': 1
        }

    def current_token(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def consume(self, expected_type=None):
        token = self.current_token()
        if token is None:
            raise Exception("Unexpected end of input")
        if expected_type and token.type != expected_type:
            raise Exception(f"Expected {expected_type}, got {token.type}")
        self.pos += 1
        return token

    def peek(self, expected_type):
        token = self.current_token()
        return token and token.type == expected_type


# ============================================================================
# C CODE GENERATOR
# ============================================================================

class CCodeGenerator:
    """Generate C code from DSL"""

    def __init__(self):
        self.scanner = Scanner()
        self.c_code = []
        self.indent_level = 0
        self.variables = set()
        self.arrays = set()

        # Unit conversion factors (to base unit)
        self.conversions = {
            'mg': 0.001, 'cg': 0.01, 'dg': 0.1, 'g': 1,
            'dag': 10, 'hg': 100, 'kg': 1000, 't': 1000000,
            'mm': 0.001, 'cm': 0.01, 'dm': 0.1, 'm': 1,
            'dam': 10, 'hm': 100, 'km': 1000,
            'ms': 0.001, 's': 1, 'min': 60, 'hr': 3600,
            'd': 86400, 'wk': 604800, 'mo': 2592000, 'yr': 31536000,
            'ml': 0.001, 'cl': 0.01, 'dl': 0.1, 'l': 1
        }

        self.unit_categories = {
            'weight': ['mg', 'cg', 'dg', 'g', 'dag', 'hg', 'kg', 't'],
            'distance': ['mm', 'cm', 'dm', 'm', 'dam', 'hm', 'km'],
            'time': ['ms', 's', 'min', 'hr', 'd', 'wk', 'mo', 'yr'],
            'fluid': ['ml', 'cl', 'dl', 'l']
        }

    def emit(self, code):
        """Emit C code with proper indentation"""
        indent = "    " * self.indent_level
        self.c_code.append(indent + code)

    def generate(self, source_code):
        """Main generation function"""
        tokens = self.scanner.scan(source_code)
        self.tokens = tokens
        self.pos = 0

        # Generate C code
        self.emit("#include <stdio.h>")
        self.emit("#include <stdlib.h>")
        self.emit("")
        self.emit("int main() {")
        self.indent_level += 1

        # Parse program
        self.parse_program()

        self.emit("return 0;")
        self.indent_level -= 1
        self.emit("}")

        return "\n".join(self.c_code)

    def current_token(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def consume(self, expected_type=None):
        token = self.current_token()
        if token is None:
            return None
        if expected_type and token.type != expected_type:
            raise Exception(f"Expected {expected_type}, got {token.type}")
        self.pos += 1
        return token

    def peek(self, expected_type):
        token = self.current_token()
        return token and token.type == expected_type

    def parse_program(self):
        """Parse entire program"""
        while self.current_token():
            self.parse_statement()

    def parse_statement(self):
        """Parse a statement"""
        token = self.current_token()

        if not token:
            return

        if token.type == 'IDENTIFIER':
            self.parse_assignment()
        elif token.type == 'CONVERT':
            self.parse_conversion()
        elif token.type == 'PRINT':
            self.parse_print()
        elif token.type == 'IF':
            self.parse_if()
        elif token.type == 'FOR':
            self.parse_for()
        else:
            self.pos += 1  # Skip unknown token

    def parse_assignment(self):
        """Parse: identifier = expression [unit]"""
        var_name = self.consume('IDENTIFIER').value
        self.consume('ASSIGN')

        expr, has_unit = self.parse_expression()

        # Declare variable if first use
        if var_name not in self.variables:
            self.variables.add(var_name)
            self.emit(f"double {var_name};")

        self.emit(f"{var_name} = {expr};")

    def parse_conversion(self):
        """Parse: convert identifier to unit"""
        self.consume('CONVERT')
        var_name = self.consume('IDENTIFIER').value
        self.consume('TO')
        target_unit = self.consume('UNIT').value

        # Find which category this unit belongs to
        category = None
        for cat, units in self.unit_categories.items():
            if target_unit in units:
                category = cat
                break

        if category:
            conversion_factor = self.conversions[target_unit]
            self.emit(f"// Convert {var_name} to {target_unit}")
            self.emit(f"{var_name} = {var_name} / {conversion_factor};")

    def parse_print(self):
        """Parse: print expression"""
        self.consume('PRINT')
        expr, has_unit = self.parse_expression()
        self.emit(f'printf("%f\\n", {expr});')

    def parse_if(self):
        """Parse: if condition then { statements } [else { statements }]"""
        self.consume('IF')
        condition = self.parse_condition()
        self.consume('THEN')

        self.emit(f"if ({condition}) {{")
        self.indent_level += 1

        self.consume('LBRACE')
        while not self.peek('RBRACE'):
            self.parse_statement()
        self.consume('RBRACE')

        self.indent_level -= 1

        if self.peek('ELSE'):
            self.emit("} else {")
            self.indent_level += 1

            self.consume('ELSE')
            self.consume('LBRACE')
            while not self.peek('RBRACE'):
                self.parse_statement()
            self.consume('RBRACE')

            self.indent_level -= 1

        self.emit("}")

    def parse_for(self):
        """Parse: for identifier in [list] do { statements }"""
        self.consume('FOR')
        loop_var = self.consume('IDENTIFIER').value
        self.consume('IN')

        # Parse list
        self.consume('LBRACKET')
        list_items = []

        while not self.peek('RBRACKET'):
            expr, _ = self.parse_expression()
            list_items.append(expr)
            if self.peek('COMMA'):
                self.consume('COMMA')

        self.consume('RBRACKET')
        self.consume('DO')

        # Generate array
        array_name = f"arr_{loop_var}"
        self.arrays.add(array_name)
        items_str = ", ".join(list_items)
        self.emit(f"double {array_name}[] = {{{items_str}}};")
        self.emit(f"int {array_name}_size = {len(list_items)};")

        # Generate loop
        if loop_var not in self.variables:
            self.variables.add(loop_var)

        self.emit(f"for (int i = 0; i < {array_name}_size; i++) {{")
        self.indent_level += 1
        self.emit(f"double {loop_var} = {array_name}[i];")

        self.consume('LBRACE')
        while not self.peek('RBRACE'):
            self.parse_statement()
        self.consume('RBRACE')

        self.indent_level -= 1
        self.emit("}")

    def parse_condition(self):
        """Parse: expression comparison_op expression"""
        left, _ = self.parse_expression()

        op_token = self.current_token()
        if op_token.type in ['EQ', 'NE', 'GT', 'LT', 'GE', 'LE']:
            op_map = {
                'EQ': '==', 'NE': '!=', 'GT': '>',
                'LT': '<', 'GE': '>=', 'LE': '<='
            }
            op = op_map[op_token.type]
            self.consume()
        else:
            raise Exception(f"Expected comparison operator, got {op_token.type}")

        right, _ = self.parse_expression()

        return f"{left} {op} {right}"

    def parse_expression(self):
        """Parse: term [(+|-) term]*"""
        result, has_unit = self.parse_term()

        while self.peek('PLUS') or self.peek('MINUS'):
            op = self.consume()
            term, _ = self.parse_term()
            result = f"({result} {op.value} {term})"

        return result, has_unit

    def parse_term(self):
        """Parse: factor [(*|/) factor]*"""
        result, has_unit = self.parse_factor()

        while self.peek('MULTIPLY') or self.peek('DIVIDE'):
            op = self.consume()
            factor, _ = self.parse_factor()
            result = f"({result} {op.value} {factor})"

        return result, has_unit

    def parse_factor(self):
        """Parse: number [unit] | identifier | (expression)"""
        token = self.current_token()

        if token.type == 'NUMBER':
            num = self.consume().value

            # Check for unit
            if self.peek('UNIT'):
                unit = self.consume('UNIT').value
                # Convert to base unit
                factor = self.conversions.get(unit, 1)
                return f"({num} * {factor})", True

            return num, False

        elif token.type == 'IDENTIFIER':
            var_name = self.consume().value
            return var_name, False

        elif token.type == 'LPAREN':
            self.consume('LPAREN')
            expr, has_unit = self.parse_expression()
            self.consume('RPAREN')
            return f"({expr})", has_unit

        else:
            raise Exception(f"Unexpected token in factor: {token.type}")


# ============================================================================
# VALIDATION AND TESTING
# ============================================================================

def validate_c_code(c_code):
    """Validate generated C code"""
    issues = []

    # Check for basic C syntax elements
    if "#include <stdio.h>" not in c_code:
        issues.append("Missing stdio.h include")

    if "int main()" not in c_code:
        issues.append("Missing main function")

    if "return 0;" not in c_code:
        issues.append("Missing return statement in main")

    # Check for balanced braces
    open_braces = c_code.count('{')
    close_braces = c_code.count('}')
    if open_braces != close_braces:
        issues.append(f"Unbalanced braces: {open_braces} open, {close_braces} close")

    # Check for balanced parentheses
    open_parens = c_code.count('(')
    close_parens = c_code.count(')')
    if open_parens != close_parens:
        issues.append(f"Unbalanced parentheses: {open_parens} open, {close_parens} close")

    return issues


def compile_and_run_c(c_code, test_name):
    """Compile and run C code"""
    import subprocess
    import os

    # Write C code to file
    c_filename = f"test_{test_name}.c"
    exe_filename = f"test_{test_name}.exe"

    with open(c_filename, 'w') as f:
        f.write(c_code)

    print(f"\n{'=' * 60}")
    print(f"Compiling {c_filename}...")
    print('=' * 60)

    # Compile
    compile_result = subprocess.run(
        ['gcc', c_filename, '-o', exe_filename],
        capture_output=True,
        text=True
    )

    if compile_result.returncode != 0:
        print("COMPILATION FAILED:")
        print(compile_result.stderr)
        return None

    print("✓ Compilation successful")

    # Run
    print(f"\nRunning {exe_filename}...")
    print('-' * 60)
    run_result = subprocess.run(
        [f'./{exe_filename}' if os.name != 'nt' else exe_filename],
        capture_output=True,
        text=True
    )

    print("OUTPUT:")
    print(run_result.stdout)

    if run_result.stderr:
        print("ERRORS:")
        print(run_result.stderr)

    return run_result.stdout


# ============================================================================
# MAIN TEST PROGRAM
# ============================================================================

def main():
    """Test C code generation"""

    test_programs = [
        ("simple_assignment", "x = 5 kg\nprint x"),
        ("conversion", "x = 100 kg\nconvert x to g\nprint x"),
        ("arithmetic", "result = 10 + 20 * 3\nprint result"),
        ("if_statement", "x = 15\nif x > 10 then {\n    print x\n}"),
        ("if_else", "x = 5\nif x > 10 then {\n    y = 1\n} else {\n    y = 0\n}\nprint y"),
        ("for_loop", "for i in [1, 2, 3] do {\n    print i\n}"),
    ]

    generator = CCodeGenerator()

    for test_name, dsl_code in test_programs:
        print("\n" + "=" * 80)
        print(f"TEST: {test_name}")
        print("=" * 80)
        print("DSL Code:")
        print(dsl_code)
        print("\n" + "-" * 80)

        try:
            # Generate C code
            c_code = generator.generate(dsl_code)

            print("Generated C Code:")
            print("-" * 80)
            print(c_code)

            # Validate
            print("\n" + "-" * 80)
            print("Validation:")
            print("-" * 80)
            issues = validate_c_code(c_code)
            if issues:
                print("⚠ Issues found:")
                for issue in issues:
                    print(f"  - {issue}")
            else:
                print("✓ No issues found")

            # Save to file
            with open(f"{test_name}.c", 'w') as f:
                f.write(c_code)
            print(f"✓ Saved to {test_name}.c")

            # Try to compile and run (optional)
            # compile_and_run_c(c_code, test_name)

        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()

        # Reset generator for next test
        generator = CCodeGenerator()


if __name__ == "__main__":
    main()