"""
Finite Automata Implementation for Unit Conversion Language
Lexical Analyzers for Identifiers and Constants
"""


class IdentifierFA:
    """
    Finite Automaton for recognizing identifiers
    Language: [a-zA-Z][a-zA-Z0-9]*
    """

    def __init__(self):
        self.state = 'q0'  # Initial state

    def reset(self):
        """Reset automaton to initial state"""
        self.state = 'q0'

    def is_letter(self, char):
        """Check if character is a letter"""
        return char.isalpha()

    def is_digit(self, char):
        """Check if character is a digit"""
        return char.isdigit()

    def transition(self, char):
        """
        Transition function δ
        q0 --letter--> q1
        q1 --letter/digit--> q1
        """
        if self.state == 'q0':
            if self.is_letter(char):
                self.state = 'q1'
                return True
            else:
                return False  # Reject

        elif self.state == 'q1':
            if self.is_letter(char) or self.is_digit(char):
                self.state = 'q1'
                return True
            else:
                return False  # Reject

        return False

    def is_accepting(self):
        """Check if current state is accepting"""
        return self.state == 'q1'

    def recognize(self, string):
        """
        Recognize if string is a valid identifier
        Returns: (bool, str) - (accepted, error_message)
        """
        if not string:
            return False, "Empty string is not a valid identifier"

        self.reset()

        for i, char in enumerate(string):
            if not self.transition(char):
                return False, f"Rejected at position {i}: '{char}' is invalid"

        if self.is_accepting():
            return True, "Valid identifier"
        else:
            return False, "String not accepted"


class ConstantFA:
    """
    Finite Automaton for recognizing integer constants
    Language: 0 | -?[1-9][0-9]*
    """

    def __init__(self):
        self.state = 'q0'  # Initial state

    def reset(self):
        """Reset automaton to initial state"""
        self.state = 'q0'

    def is_zero(self, char):
        """Check if character is zero"""
        return char == '0'

    def is_nonzero_digit(self, char):
        """Check if character is non-zero digit (1-9)"""
        return char in '123456789'

    def is_digit(self, char):
        """Check if character is any digit (0-9)"""
        return char.isdigit()

    def is_minus(self, char):
        """Check if character is minus sign"""
        return char == '-'

    def transition(self, char):
        """
        Transition function δ
        q0 --'0'--> q2 (accept)
        q0 --'1-9'--> q3 (accept)
        q0 --'-'--> q1
        q1 --'1-9'--> q3 (accept)
        q3 --'0-9'--> q3
        """
        if self.state == 'q0':
            if self.is_zero(char):
                self.state = 'q2'  # Standalone zero
                return True
            elif self.is_nonzero_digit(char):
                self.state = 'q3'  # Positive integer
                return True
            elif self.is_minus(char):
                self.state = 'q1'  # Minus sign
                return True
            else:
                return False  # Reject

        elif self.state == 'q1':
            # After minus, only non-zero digits allowed
            if self.is_nonzero_digit(char):
                self.state = 'q3'
                return True
            else:
                return False  # Reject (no -0 or -01)

        elif self.state == 'q2':
            # After standalone zero, no more digits allowed
            return False  # Reject (no leading zeros)

        elif self.state == 'q3':
            # Can continue with any digit
            if self.is_digit(char):
                self.state = 'q3'
                return True
            else:
                return False  # Reject

        return False

    def is_accepting(self):
        """Check if current state is accepting (q2 or q3)"""
        return self.state in ['q2', 'q3']

    def recognize(self, string):
        """
        Recognize if string is a valid constant
        Returns: (bool, str) - (accepted, error_message)
        """
        if not string:
            return False, "Empty string is not a valid constant"

        self.reset()

        for i, char in enumerate(string):
            if not self.transition(char):
                return False, f"Rejected at position {i}: '{char}' is invalid in state {self.state}"

        if self.is_accepting():
            return True, "Valid constant"
        else:
            return False, f"String not accepted (ended in non-accepting state {self.state})"


def test_identifiers():
    """Test suite for identifier FA"""
    print("=" * 60)
    print("TESTING IDENTIFIER FINITE AUTOMATON")
    print("=" * 60)

    fa = IdentifierFA()

    # Valid identifiers
    valid_tests = [
        "x",
        "temp",
        "value1",
        "myVar2",
        "A",
        "distance",
        "var123abc",
        "CamelCase",
        "snake_case"  # Note: this will fail if underscore not in alphabet
    ]

    print("\n--- Valid Identifier Tests ---")
    for test in valid_tests:
        result, message = fa.recognize(test)
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: '{test}' - {message}")

    # Invalid identifiers
    invalid_tests = [
        "1var",  # starts with digit
        "123",  # all digits
        "_test",  # starts with underscore
        "my-var",  # contains hyphen
        "",  # empty string
        "9abc"  # starts with digit
    ]

    print("\n--- Invalid Identifier Tests ---")
    for test in invalid_tests:
        result, message = fa.recognize(test)
        status = "✓ PASS" if not result else "✗ FAIL"
        print(f"{status}: '{test}' - {message}")


def test_constants():
    """Test suite for constant FA"""
    print("\n" + "=" * 60)
    print("TESTING CONSTANT FINITE AUTOMATON")
    print("=" * 60)

    fa = ConstantFA()

    # Valid constants
    valid_tests = [
        "0",
        "5",
        "42",
        "123",
        "-7",
        "-123",
        "1000",
        "999999"
    ]

    print("\n--- Valid Constant Tests ---")
    for test in valid_tests:
        result, message = fa.recognize(test)
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: '{test}' - {message}")

    # Invalid constants
    invalid_tests = [
        "00",  # leading zero
        "01",  # leading zero
        "007",  # leading zeros
        "-0",  # negative zero
        "+5",  # plus sign
        "",  # empty string
        "-",  # just minus
        "12.5",  # decimal (not in this grammar)
        "abc"  # letters
    ]

    print("\n--- Invalid Constant Tests ---")
    for test in invalid_tests:
        result, message = fa.recognize(test)
        status = "✓ PASS" if not result else "✗ FAIL"
        print(f"{status}: '{test}' - {message}")


def interactive_mode():
    """Interactive testing mode"""
    print("\n" + "=" * 60)
    print("INTERACTIVE MODE")
    print("=" * 60)
    print("Commands:")
    print("  'i <string>' - test identifier")
    print("  'c <string>' - test constant")
    print("  'q' - quit")
    print()

    id_fa = IdentifierFA()
    const_fa = ConstantFA()

    while True:
        user_input = input("Enter command: ").strip()

        if user_input.lower() == 'q':
            break

        if not user_input:
            continue

        parts = user_input.split(maxsplit=1)
        if len(parts) != 2:
            print("Invalid command format")
            continue

        cmd, test_string = parts

        if cmd.lower() == 'i':
            result, message = id_fa.recognize(test_string)
            print(f"Identifier: '{test_string}' - {message}")
        elif cmd.lower() == 'c':
            result, message = const_fa.recognize(test_string)
            print(f"Constant: '{test_string}' - {message}")
        else:
            print("Unknown command. Use 'i' or 'c'")
        print()


if __name__ == "__main__":
    # Run test suites
    test_identifiers()
    test_constants()

    # Optional: Interactive mode
    # interactive_mode()