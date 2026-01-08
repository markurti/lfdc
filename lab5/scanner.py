class Token:

    def __init__(self, token_type, value, line, column):
        self.type = token_type
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Token({self.type}, '{self.value}', {self.line}:{self.column})"


class IdentifierFA:
    """FA for identifiers"""

    def recognize(self, string):
        if not string:
            return False

        # First character must be a letter
        if not string[0].isalpha():
            return False

        # Rest can be letters or digits
        for char in string[1:]:
            if not (char.isalpha() or char.isdigit()):
                return False

        return True


class ConstantFA:
    """FA for constants"""

    def recognize(self, string):
        if not string:
            return False

        # Special case: standalone "0"
        if string == "0":
            return True

        # Check for optional minus sign
        start_idx = 0
        if string[0] == '-':
            if len(string) == 1:  # just "-"
                return False
            start_idx = 1

        # First digit after optional minus must be non-zero
        if string[start_idx] not in '123456789':
            return False

        # Rest must be digits
        for char in string[start_idx + 1:]:
            if not char.isdigit():
                return False

        return True


class Scanner:
    """
    Scanner uses FA for identifiers and constants
    """

    def __init__(self, source_code):
        self.source = source_code
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens = []

        # Finite Automata
        self.identifier_fa = IdentifierFA()
        self.constant_fa = ConstantFA()

        # Keywords
        self.keywords = {
            'convert', 'to', 'print', 'if', 'then', 'else',
            'for', 'in', 'do'
        }

        # Units
        self.units = {
            'ml', 'cl', 'dl', 'l',
            'mm', 'cm', 'dm', 'm', 'dam', 'hm', 'km',
            'ms', 's', 'min', 'hr', 'd', 'wk', 'mo', 'yr',
            'mg', 'cg', 'dg', 'g', 'dag', 'hg', 'kg', 't'
        }

    def current_char(self):
        """Get current character"""
        if self.pos >= len(self.source):
            return None
        return self.source[self.pos]

    def peek(self, offset=1):
        """Look ahead at character"""
        pos = self.pos + offset
        if pos >= len(self.source):
            return None
        return self.source[pos]

    def advance(self):
        """Move to next character"""
        if self.pos < len(self.source):
            if self.source[self.pos] == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
            self.pos += 1

    def skip_whitespace(self):
        """Skip whitespace characters"""
        while self.current_char() and self.current_char().isspace():
            self.advance()

    def scan_number_or_minus(self):
        """Scan number or minus operator using Constant FA"""
        start_pos = self.pos
        start_col = self.column
        lexeme = ""

        # Check if it starts with minus
        if self.current_char() == '-':
            lexeme += self.current_char()
            self.advance()

            # If next character is a digit, try to match as number
            if self.current_char() and self.current_char().isdigit():
                while self.current_char() and self.current_char().isdigit():
                    lexeme += self.current_char()
                    self.advance()

                # Validate with FA
                if self.constant_fa.recognize(lexeme):
                    return Token('NUMBER', lexeme, self.line, start_col)
                else:
                    return Token('ERROR', lexeme, self.line, start_col)
            else:
                # Just a minus operator
                return Token('MINUS', '-', self.line, start_col)

        # Positive number
        while self.current_char() and self.current_char().isdigit():
            lexeme += self.current_char()
            self.advance()

        # Validate with FA
        if self.constant_fa.recognize(lexeme):
            return Token('NUMBER', lexeme, self.line, start_col)
        else:
            return Token('ERROR', lexeme, self.line, start_col)

    def scan_identifier_or_keyword(self):
        """Scan identifier or keyword using Identifier FA"""
        start_col = self.column
        lexeme = ""

        # Collect alphanumeric characters
        while self.current_char() and (self.current_char().isalnum() or self.current_char() == '_'):
            lexeme += self.current_char()
            self.advance()

        # Validate with FA
        if not self.identifier_fa.recognize(lexeme):
            return Token('ERROR', lexeme, self.line, start_col)

        # Check if it's a keyword
        if lexeme in self.keywords:
            return Token('KEYWORD', lexeme, self.line, start_col)

        # Check if it's a unit
        if lexeme in self.units:
            return Token('UNIT', lexeme, self.line, start_col)

        # It's an identifier
        return Token('IDENTIFIER', lexeme, self.line, start_col)

    def scan_token(self):
        """Scan next token"""
        self.skip_whitespace()

        if self.current_char() is None:
            return None

        start_col = self.column
        char = self.current_char()
        next_char = self.peek()

        # Identifier and keyword starting with number (error)
        if char.isdigit():
            if (next_char is not None) and next_char.isalpha():
                return self.scan_identifier_or_keyword()

        # Numbers and minus
        if char.isdigit():
            return self.scan_number_or_minus()

        if char == '-':
            return self.scan_number_or_minus()

        # Identifiers and keywords
        if char.isalpha():
            return self.scan_identifier_or_keyword()

        # Single character tokens
        single_char_tokens = {
            '=': 'ASSIGN',
            '+': 'PLUS',
            '*': 'MULTIPLY',
            '/': 'DIVIDE',
            '(': 'LPAREN',
            ')': 'RPAREN',
            '{': 'LBRACE',
            '}': 'RBRACE',
            '[': 'LBRACKET',
            ']': 'RBRACKET',
            ',': 'COMMA'
        }

        if char in single_char_tokens:
            self.advance()
            return Token(single_char_tokens[char], char, self.line, start_col)

        # Two character tokens
        if char == '=' and self.peek() == '=':
            self.advance()
            self.advance()
            return Token('EQUAL', '==', self.line, start_col)

        if char == '!' and self.peek() == '=':
            self.advance()
            self.advance()
            return Token('NOT_EQUAL', '!=', self.line, start_col)

        if char == '>' and self.peek() == '=':
            self.advance()
            self.advance()
            return Token('GREATER_EQUAL', '>=', self.line, start_col)

        if char == '<' and self.peek() == '=':
            self.advance()
            self.advance()
            return Token('LESS_EQUAL', '<=', self.line, start_col)

        if char == '>':
            self.advance()
            return Token('GREATER', '>', self.line, start_col)

        if char == '<':
            self.advance()
            return Token('LESS', '<', self.line, start_col)

        # Unknown character
        self.advance()
        return Token('ERROR', char, self.line, start_col)

    def scan(self):
        """Scan entire source code and return list of tokens"""
        self.tokens = []

        while True:
            token = self.scan_token()
            if token is None:
                break
            self.tokens.append(token)

        return self.tokens


def main():
    """Test the scanner"""

    # Test cases
    test_programs = [
        # Test 1: Simple assignment
        """x = 5 kg""",

        # Test 2: Conversion
        """convert distance to km""",

        # Test 3: Identifiers and numbers
        """value1 = 100
        myVar = -50
        temp = 0""",

        # Test 4: Invalid identifiers (start with digit)
        """1var = 5""",

        # Test 5: Invalid constants (leading zeros)
        """x = 007""",

        # Test 6: Complex expression
        """result = (a + b) * 2
        print result""",

        # Test 7: If statement
        """if x > 10 then {
            print x
        }""",

        # Test 8: All comparison operators
        """a == b
        c != d
        e > f
        g < h
        i >= j
        k <= l"""
    ]

    for i, program in enumerate(test_programs, 1):
        print("=" * 70)
        print(f"TEST {i}")
        print("=" * 70)
        print("Source Code:")
        print(program)
        print("\n" + "-" * 70)
        print("Tokens:")
        print("-" * 70)

        scanner = Scanner(program)
        tokens = scanner.scan()

        for token in tokens:
            print(token)

        print()


if __name__ == "__main__":
    main()