"""
LL(1) Parser for Unit Conversion Language
Implements LL(1) parsing algorithm with parse tree output
"""

from collections import defaultdict
import re


# ============================================================================
# SCANNER (Lexer) - Produces PIF (Program Internal Form)
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

        # Token patterns (order matters)
        self.patterns = [
            ('NUMBER', r'0|[1-9][0-9]*'),
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
        """Scan source and return PIF (Program Internal Form)"""
        pif = []
        position = 0

        while position < len(source_code):
            matched = False

            for token_type, pattern in self.patterns:
                regex = re.compile(pattern)
                match = regex.match(source_code, position)

                if match:
                    value = match.group(0)

                    # Skip whitespace
                    if token_type == 'WHITESPACE':
                        position = match.end()
                        matched = True
                        break

                    # Classify IDENTIFIER
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

        pif.append(Token('$', '$', position))  # End marker
        return pif


# ============================================================================
# LL(1) GRAMMAR DEFINITION
# ============================================================================

class Grammar:
    """
    LL(1) Grammar for Unit Conversion Language
    Transformed to eliminate left recursion and left factoring
    """

    def __init__(self):
        # Non-terminals
        self.non_terminals = {
            'program', 'stmt_list', 'stmt_list_tail', 'statement',
            'assign_stmt', 'conv_stmt', 'print_stmt', 'if_stmt', 'for_stmt',
            'else_opt', 'block', 'condition', 'comp_op',
            'list_expr', 'list_elems', 'list_tail',
            'expression', 'expr_tail', 'term', 'term_tail', 'factor', 'unit_opt'
        }

        # Terminals
        self.terminals = {
            'IDENTIFIER', 'NUMBER', 'UNIT',
            'CONVERT', 'TO', 'PRINT', 'IF', 'THEN', 'ELSE', 'FOR', 'IN', 'DO',
            'ASSIGN', 'PLUS', 'MINUS', 'MULTIPLY', 'DIVIDE',
            'EQ', 'NE', 'GT', 'LT', 'GE', 'LE',
            'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE', 'LBRACKET', 'RBRACKET', 'COMMA',
            'epsilon', '$'
        }

        # Start symbol
        self.start_symbol = 'program'

        # Productions: non_terminal -> [list of symbols]
        self.productions = {
            'program': [
                ['stmt_list']
            ],
            'stmt_list': [
                ['statement', 'stmt_list_tail']
            ],
            'stmt_list_tail': [
                ['statement', 'stmt_list_tail'],
                ['epsilon']
            ],
            'statement': [
                ['assign_stmt'],
                ['conv_stmt'],
                ['print_stmt'],
                ['if_stmt'],
                ['for_stmt']
            ],
            'assign_stmt': [
                ['IDENTIFIER', 'ASSIGN', 'expression']
            ],
            'conv_stmt': [
                ['CONVERT', 'IDENTIFIER', 'TO', 'UNIT']
            ],
            'print_stmt': [
                ['PRINT', 'expression']
            ],
            'if_stmt': [
                ['IF', 'condition', 'THEN', 'block', 'else_opt']
            ],
            'else_opt': [
                ['ELSE', 'block'],
                ['epsilon']
            ],
            'for_stmt': [
                ['FOR', 'IDENTIFIER', 'IN', 'list_expr', 'DO', 'block']
            ],
            'block': [
                ['LBRACE', 'stmt_list', 'RBRACE']
            ],
            'condition': [
                ['expression', 'comp_op', 'expression']
            ],
            'comp_op': [
                ['EQ'], ['NE'], ['GT'], ['LT'], ['GE'], ['LE']
            ],
            'list_expr': [
                ['LBRACKET', 'list_elems', 'RBRACKET']
            ],
            'list_elems': [
                ['expression', 'list_tail'],
                ['epsilon']
            ],
            'list_tail': [
                ['COMMA', 'expression', 'list_tail'],
                ['epsilon']
            ],
            'expression': [
                ['term', 'expr_tail']
            ],
            'expr_tail': [
                ['PLUS', 'term', 'expr_tail'],
                ['MINUS', 'term', 'expr_tail'],
                ['epsilon']
            ],
            'term': [
                ['factor', 'term_tail']
            ],
            'term_tail': [
                ['MULTIPLY', 'factor', 'term_tail'],
                ['DIVIDE', 'factor', 'term_tail'],
                ['epsilon']
            ],
            'factor': [
                ['NUMBER', 'unit_opt'],
                ['IDENTIFIER'],
                ['LPAREN', 'expression', 'RPAREN']
            ],
            'unit_opt': [
                ['UNIT'],
                ['epsilon']
            ]
        }

        # FIRST sets
        self.first = {}
        self.compute_first()

        # FOLLOW sets
        self.follow = {}
        self.compute_follow()

        # Parsing table
        self.parsing_table = {}
        self.build_parsing_table()

    def compute_first(self):
        """Compute FIRST sets for all non-terminals"""
        # Initialize
        for nt in self.non_terminals:
            self.first[nt] = set()

        # Iterate until no changes
        changed = True
        while changed:
            changed = False
            for non_terminal, productions in self.productions.items():
                for production in productions:
                    old_size = len(self.first[non_terminal])

                    # Calculate FIRST of production
                    first_of_prod = self.first_of_sequence(production)
                    self.first[non_terminal].update(first_of_prod)

                    if len(self.first[non_terminal]) > old_size:
                        changed = True

    def first_of_sequence(self, sequence):
        """Calculate FIRST set of a sequence of symbols"""
        result = set()

        for symbol in sequence:
            if symbol == 'epsilon':
                result.add('epsilon')
                break
            elif symbol in self.terminals:
                result.add(symbol)
                break
            elif symbol in self.non_terminals:
                symbol_first = self.first.get(symbol, set())
                result.update(symbol_first - {'epsilon'})
                if 'epsilon' not in symbol_first:
                    break
        else:
            # All symbols can derive epsilon
            result.add('epsilon')

        return result

    def compute_follow(self):
        """Compute FOLLOW sets for all non-terminals"""
        # Initialize
        for nt in self.non_terminals:
            self.follow[nt] = set()

        # $ is in FOLLOW of start symbol
        self.follow[self.start_symbol].add('$')

        # Iterate until no changes
        changed = True
        while changed:
            changed = False
            for non_terminal, productions in self.productions.items():
                for production in productions:
                    for i, symbol in enumerate(production):
                        if symbol in self.non_terminals:
                            old_size = len(self.follow[symbol])

                            # Calculate FIRST of what comes after
                            rest = production[i + 1:]
                            if rest:
                                first_of_rest = self.first_of_sequence(rest)
                                self.follow[symbol].update(first_of_rest - {'epsilon'})
                                if 'epsilon' in first_of_rest:
                                    self.follow[symbol].update(self.follow[non_terminal])
                            else:
                                self.follow[symbol].update(self.follow[non_terminal])

                            if len(self.follow[symbol]) > old_size:
                                changed = True

    def build_parsing_table(self):
        """Build LL(1) parsing table"""
        for non_terminal, productions in self.productions.items():
            for prod_idx, production in enumerate(productions):
                # For each terminal in FIRST(production)
                first_of_prod = self.first_of_sequence(production)

                for terminal in first_of_prod:
                    if terminal != 'epsilon':
                        key = (non_terminal, terminal)
                        if key in self.parsing_table:
                            print(f"Warning: Grammar is not LL(1) - conflict at {key}")
                        self.parsing_table[key] = (prod_idx, production)

                # If epsilon in FIRST(production), add for FOLLOW terminals
                if 'epsilon' in first_of_prod:
                    for terminal in self.follow[non_terminal]:
                        key = (non_terminal, terminal)
                        if key in self.parsing_table:
                            print(f"Warning: Grammar is not LL(1) - conflict at {key}")
                        self.parsing_table[key] = (prod_idx, production)

    def get_production(self, non_terminal, terminal):
        """Get production from parsing table"""
        return self.parsing_table.get((non_terminal, terminal))


# ============================================================================
# PARSE TREE NODE
# ============================================================================

class TreeNode:
    """Node in parse tree with father-sibling representation"""
    node_counter = 0

    def __init__(self, symbol, value=None):
        self.id = TreeNode.node_counter
        TreeNode.node_counter += 1
        self.symbol = symbol
        self.value = value
        self.father = None  # Parent node
        self.sibling = None  # Right sibling
        self.child = None  # Leftmost child

    def add_child(self, child_node):
        """Add a child to this node"""
        child_node.father = self
        if self.child is None:
            self.child = child_node
        else:
            # Add as sibling to existing children
            current = self.child
            while current.sibling is not None:
                current = current.sibling
            current.sibling = child_node

    def __repr__(self):
        if self.value:
            return f"{self.symbol}({self.value})"
        return self.symbol


# ============================================================================
# LL(1) PARSER
# ============================================================================

class LL1Parser:
    """LL(1) Parser implementation"""

    def __init__(self, grammar):
        self.grammar = grammar
        self.stack = []
        self.input_tokens = []
        self.input_index = 0
        self.parse_tree_root = None
        self.productions_used = []

    def parse(self, pif):
        """Parse PIF and build parse tree"""
        TreeNode.node_counter = 0  # Reset counter
        self.input_tokens = pif
        self.input_index = 0
        self.productions_used = []

        # Initialize stack with start symbol
        root = TreeNode(self.grammar.start_symbol)
        self.parse_tree_root = root
        self.stack = [('$', None), (self.grammar.start_symbol, root)]

        print("\n" + "=" * 80)
        print("LL(1) PARSING TRACE")
        print("=" * 80)
        print(f"{'Step':<6} {'Stack':<30} {'Input':<30} {'Action'}")
        print("-" * 80)

        step = 0
        while len(self.stack) > 0:
            step += 1

            # Current stack top
            top_symbol, top_node = self.stack[-1]

            # Current input token
            current_token = self.input_tokens[self.input_index]

            # Display state
            stack_str = ' '.join([s for s, _ in self.stack[-5:]])  # Show last 5
            input_str = ' '.join([t.type for t in self.input_tokens[self.input_index:self.input_index + 3]])

            # Match or expand
            if top_symbol == current_token.type or (top_symbol == '$' and current_token.type == '$'):
                # Match
                action = f"Match {top_symbol}"
                print(f"{step:<6} {stack_str:<30} {input_str:<30} {action}")

                # Update tree node value if it's a terminal
                if top_node and top_symbol != '$':
                    top_node.value = current_token.value

                self.stack.pop()
                self.input_index += 1

            elif top_symbol == 'epsilon':
                # Epsilon - just pop from stack
                action = "Pop epsilon"
                print(f"{step:<6} {stack_str:<30} {input_str:<30} {action}")
                self.stack.pop()

            elif top_symbol in self.grammar.non_terminals:
                # Non-terminal - expand using parsing table
                production = self.grammar.get_production(top_symbol, current_token.type)

                if production is None:
                    raise Exception(f"Syntax error at position {current_token.position}: "
                                    f"Unexpected token {current_token.type} ('{current_token.value}')")

                prod_idx, prod_symbols = production
                action = f"Apply {top_symbol} -> {' '.join(prod_symbols)}"
                print(f"{step:<6} {stack_str:<30} {input_str:<30} {action}")

                # Record production
                self.productions_used.append(f"{top_symbol} -> {' '.join(prod_symbols)}")

                # Pop non-terminal from stack
                self.stack.pop()

                # Create child nodes and push to stack (in reverse order)
                child_nodes = []
                for symbol in prod_symbols:
                    child_node = TreeNode(symbol)
                    child_nodes.append(child_node)
                    top_node.add_child(child_node)

                # Push children to stack in reverse order
                for symbol, child_node in reversed(list(zip(prod_symbols, child_nodes))):
                    if symbol != 'epsilon':
                        self.stack.append((symbol, child_node))

            else:
                raise Exception(f"Unexpected symbol on stack: {top_symbol}")

        print("=" * 80)
        print("PARSING COMPLETED SUCCESSFULLY")
        print("=" * 80)

        return self.parse_tree_root

    def print_productions(self):
        """Print productions used during parsing"""
        print("\n" + "=" * 80)
        print("PRODUCTIONS USED (Derivation)")
        print("=" * 80)
        for i, prod in enumerate(self.productions_used, 1):
            print(f"{i:3}. {prod}")

    def print_parse_tree_table(self):
        """Print parse tree in father-sibling table format"""
        print("\n" + "=" * 80)
        print("PARSE TREE - FATHER-SIBLING REPRESENTATION")
        print("=" * 80)
        print(f"{'Index':<8} {'Symbol':<20} {'Value':<15} {'Father':<8} {'Sibling':<8}")
        print("-" * 80)

        # Collect all nodes using BFS
        nodes = []
        queue = [self.parse_tree_root]

        while queue:
            node = queue.pop(0)
            nodes.append(node)

            # Add children to queue
            child = node.child
            while child:
                queue.append(child)
                child = child.sibling

        # Print table
        for node in nodes:
            father_id = node.father.id if node.father else '-'
            sibling_id = node.sibling.id if node.sibling else '-'
            value_str = node.value if node.value else '-'

            print(f"{node.id:<8} {node.symbol:<20} {value_str:<15} {father_id:<8} {sibling_id:<8}")


# ============================================================================
# MAIN PROGRAM
# ============================================================================

def main():
    """Test LL(1) parser"""

    test_programs = [
        ("Simple Assignment", "x = 5 kg"),
        ("Conversion", "convert distance to km"),
        ("Print", "print x"),
        ("Expression", "result = 10 + 20 * 3"),
        ("If Statement", "if x > 10 then { print x }"),
        ("For Loop", "for i in [1, 2, 3] do { print i }"),
    ]

    scanner = Scanner()
    grammar = Grammar()
    parser = LL1Parser(grammar)

    for name, program in test_programs:
        print("\n\n")
        print("=" * 80)
        print(f"TEST: {name}")
        print("=" * 80)
        print(f"Input: {program}")

        try:
            # Scan to get PIF
            pif = scanner.scan(program)

            print("\nPIF (Program Internal Form):")
            print("-" * 80)
            for token in pif:
                print(f"  {token}")

            # Parse
            parse_tree = parser.parse(pif)

            # Output
            parser.print_productions()
            parser.print_parse_tree_table()

        except Exception as e:
            print(f"\nERROR: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()