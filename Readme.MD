# LFDC - Formal Languages and Compiler Design

Labs for Formal Languages and Compiler Design course.

## Labs Overview

- **Lab 1**: Mini DSL Grammar Definition
- **Lab 2**: Finite Automata (FA) and Regular Grammars (RG) for Identifiers and Constants
- **Lab 3**: Scanner Implementation with Integrated FA
- **Lab 4**: Parser Implementation (LL(1) or LR(0))
- **Lab 5**: Parsing with YACC/PLY
- **Lab 6**: LL(1) Parser Implementation
- **Lab 7**: DSL to C Translation (GenAI vs YACC Comparison)
- **Lab 8**: Grammar Optimization using GenAI

## Structure

Each lab folder contains:
- Source code (`.py` files)
- Documentation (`.txt` or `.md` files)
- Test cases and examples
- Generated outputs

## Technologies Used

- **Python 3.x**
- **PLY (Python Lex-Yacc)**
- **C** (for generated code)
- **GenAI** (ChatGPT for optimization)

## How to Run

### Scanner (Lab 3)
```bash
cd lab3
python scanner.py
```

### Parser (Lab 5/6)
```bash
cd lab5
python parser.py
```

### C Code Generator (Lab 7)
```bash
cd lab7
python genai_translator.py
python yacc_translator.py
```

## Author

Mark Urti
- GitHub: [@markurti](https://github.com/markurti)
- Repository: [lfdc](https://github.com/markurti/lfdc)

## License

Educational purposes only.