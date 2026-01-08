import re, json, sys, os


# Utilities
class SymbolTable:
    def __init__(self):
        self._map = {}  # lexeme -> index
        self._list = []  # index -> (lexeme, kind)

    def add(self, lexeme, kind):
        if lexeme in self._map:
            return self._map[lexeme]
        idx = len(self._list)
        self._map[lexeme] = idx
        self._list.append((lexeme, kind))
        return idx

    def items(self):
        return list(enumerate(self._list))

    def __str__(self):
        out = []
        for i, (lex, k) in enumerate(self._list):
            out.append(f"{i}\t{lex}\t{k}")
        return "\n".join(out)


# Build token regex from tokens.json
def build_regex(tokdef):
    # Multi-char operators must be tried before single-char -> sort by desc length
    operators = sorted(tokdef.get("operators", {}).keys(), key=lambda s: -len(s))
    delimiters = sorted(tokdef.get("delimiters", {}).keys(), key=lambda s: -len(s))
    keywords = sorted(tokdef.get("keywords", {}).keys(), key=lambda s: -len(s))
    units = sorted(tokdef.get("units", {}).keys(), key=lambda s: -len(s))

    # escape tokens for regex
    re_operators = "|".join(re.escape(op) for op in operators) if operators else None
    re_delimiters = "|".join(re.escape(d) for d in delimiters) if delimiters else None
    re_keywords = r"\b(?:" + "|".join(keywords) + r")\b" if keywords else None
    re_units = r"\b(?:" + "|".join(units) + r")\b" if units else None

    # number: optional minus, integer or decimal
    number_re = r"-?\d+(\.\d+)?"
    # string: double quotes (simple)
    string_re = r"\"([^\"\\]|\\.)*\""
    # identifier: starts with letter or underscore
    identifier_re = r"[A-Za-z][A-Za-z0-9_]*"

    parts = []
    if re_keywords:
        parts.append(f"(?P<KEYWORD>{re_keywords})")
    if re_operators:
        parts.append(f"(?P<OP>{re_operators})")
    if re_delimiters:
        parts.append(f"(?P<DELIM>{re_delimiters})")
    if re_units:
        parts.append(f"(?P<UNIT>{re_units})")

    parts.append(f"(?P<NUMBER>{number_re})")
    parts.append(f"(?P<STRING>{string_re})")
    parts.append(f"(?P<ID>{identifier_re})")

    master = "|".join(parts)
    return re.compile(master)


# Lexical analyzer
def tokenize_source(source_text, tokdef, pattern, st):
    pif = []
    errors = []
    line_no = 0
    for raw_line in source_text.splitlines():
        line_no += 1
        line = raw_line
        pos = 0
        while pos < len(line):
            # skip whitespace
            if line[pos].isspace():
                pos += 1
                continue
            m = pattern.match(line, pos)
            if not m:
                # No match -> lexical error (show token until next whitespace or known char)
                # find a segment to report
                end = pos
                while end < len(line) and not line[end].isspace():
                    end += 1
                lexeme = line[pos:end]
                errors.append(f"Lexical error: unknown token '{lexeme}' at line {line_no}")
                pos = end
                continue
            pos = m.end()
            kind = m.lastgroup
            val = m.group()
            # classify and write PIF entries using tokdef codes
            match kind:
                case "KEYWORD":
                    code = tokdef["keywords"][val]
                    pif.append((code, -1))
                case "OP":
                    code = tokdef["operators"][val]
                    pif.append((code, -1))
                case "DELIM":
                    code = tokdef["delimiters"][val]
                    pif.append((code, -1))
                case "UNIT":
                    code = tokdef["units"][val]
                    # store unit in ST
                    idx = st.add(val, "unit")
                    pif.append((code, idx))
                case "NUMBER":
                    code = tokdef["special"]["number"]
                    idx = st.add(val, "const_num")
                    pif.append((code, idx))
                case "STRING":
                    code = tokdef["special"]["string"]
                    idx = st.add(val, "const_str")
                    pif.append((code, idx))
                case "ID":
                    if val in tokdef.get("keywords", {}):
                        code = tokdef["keywords"][val]
                        pif.append((code, -1))
                    else:
                        code = tokdef["special"]["identifier"]
                        idx = st.add(val, "id")
                        pif.append((code, idx))
                case _:
                    errors.append(f"Lexical error: unknown token '{val}' at line {line_no}")
    return pif, errors


# File IO and main
def analyze_file(tokens_file, source_file):
    with open(tokens_file, "r") as f:
        tokdef = json.load(f)
    pattern = build_regex(tokdef)
    with open(source_file, "r") as f:
        src = f.read()
    st = SymbolTable()
    pif, errors = tokenize_source(src, tokdef, pattern, st)

    base = os.path.splitext(os.path.basename(source_file))[0]
    pif_file = f"PIF_{base}.txt"
    st_file = f"ST_{base}.txt"
    err_file = f"lexical_errors_{base}.txt"

    with open(pif_file, "w") as f:
        for code, idx in pif:
            f.write(f"{code} {idx}\n")
    with open(st_file, "w") as f:
        f.write(str(st))
    with open(err_file, "w") as f:
        if errors:
            f.write("\n".join(errors))
        else:
            f.write("No lexical errors found.\n")

    print(f"Output written: {pif_file}, {st_file}, {err_file}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python lexer.py tokens.json program1.mini [program2.mini ...]")
        sys.exit(1)
    tokens_file = sys.argv[1]
    print(tokens_file)
    for i in range(2, len(sys.argv)):
        analyze_file(tokens_file, sys.argv[i])
