# ============================
# LEXICAL ERROR CLASS
# ============================

class LexicalError(Exception):
    def __init__(self, message, line, column):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"{message} at line {line}, column {column}")


# ============================
# LEXICAL SPECIFICATION
# ============================

KEYWORDS = {
    "auto", "break", "case", "char", "const",
    "continue", "default", "do", "double",
    "else", "enum", "extern", "float",
    "for", "goto", "if", "int", "long",
    "register", "return", "short", "signed",
    "sizeof", "static", "struct", "switch",
    "typedef", "union", "unsigned", "void",
    "volatile", "while"
}

OPERATORS = {
    "++", "--", "==", "!=", "<=", ">=",
    "&&", "||", "+", "-", "*", "/", "%",
    "=", "<", ">", "!", "&", "|", "^"
}

DELIMITERS = {
    "(", ")", "{", "}", "[", "]",
    ";", ",", ".", ":"
}

WHITESPACE = {" ", "\t", "\n"}


# ============================
# TOKEN CLASS
# ============================

class Token:
    def __init__(self, token_type, value, line):
        self.type = token_type
        self.value = value
        self.line = line

    def __repr__(self):
        return f"<{self.type}, '{self.value}', line {self.line}>"


# ============================
# CHAR STREAM
# ============================

class CharStream:
    def __init__(self, code):
        self.code = code
        self.position = 0
        self.line = 1
        self.column = 1

    def peek(self, offset=0):
        index = self.position + offset
        if index < len(self.code):
            return self.code[index]
        return None

    def advance(self):
        char = self.peek()
        if char is None:
            return None

        self.position += 1

        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1

        return char

    def is_end(self):
        return self.position >= len(self.code)


# ============================
# LEXER
# ============================

class Lexer:

    def __init__(self, code):
        self.stream = CharStream(code)
        self.tokens = []
        self.steps = []
        self.symbol_table = {}
        self.current_decl_type = None
        self.current_state = "START"
        self.current_lexeme = ""

    def log_step(self, char, action, next_state=None, token_generated=None):
        step_info = {
            "char": char,
            "line": self.stream.line,
            "column": self.stream.column,
            "current_state": self.current_state,
            "next_state": next_state,
            "current_lexeme": self.current_lexeme,
            "action": action,
            "token_generated": token_generated,
            "symbol_table_snapshot": dict(self.symbol_table)
        }
        self.steps.append(step_info)
        if next_state:
            self.current_state = next_state

    def tokenize(self):

        while not self.stream.is_end():
            char = self.stream.peek()

            if char in WHITESPACE:
                self.log_step(char, "WHITESPACE_SKIP")
                self.stream.advance()
                continue

            if char.isalpha() or char == "_":
                self.handle_identifier()
                continue

            if char.isdigit():
                self.handle_number()
                continue

            if char in "".join(OPERATORS):
                self.handle_operator()
                continue

            if char in DELIMITERS:
                token = Token("DELIMITER", char, self.stream.line)
                self.tokens.append(token)
                self.log_step(char, "DELIMITER_FOUND",
                              token_generated=str(token))
                self.stream.advance()
                continue

            raise LexicalError(
                f"Invalid character '{char}'",
                self.stream.line,
                self.stream.column
            )

        return self.tokens

    def handle_identifier(self):

        self.current_state = "IDENTIFIER"
        self.current_lexeme = ""

        while True:
            char = self.stream.peek()
            if char and (char.isalnum() or char == "_"):
                self.current_lexeme += char
                self.log_step(char, "BUILDING_IDENTIFIER", "IDENTIFIER")
                self.stream.advance()
            else:
                break

        if self.current_lexeme in KEYWORDS:
            token_type = "KEYWORD"

            if self.current_lexeme in {"int", "float", "char", "double"}:
                self.current_decl_type = self.current_lexeme
        else:
            token_type = "IDENTIFIER"

            if self.current_lexeme not in self.symbol_table:

                size_map = {
                    "int": 4,
                    "float": 4,
                    "char": 1,
                    "double": 8
                }

                self.symbol_table[self.current_lexeme] = {
                    "type": self.current_decl_type,
                    "size": size_map.get(self.current_decl_type),
                    "declared_line": self.stream.line
                }

                self.current_decl_type = None

        token = Token(token_type, self.current_lexeme, self.stream.line)
        self.tokens.append(token)

        self.log_step(None, "TOKEN_GENERATED",
                      token_generated=str(token))

        self.current_state = "START"

    def handle_number(self):

        self.current_state = "NUMBER"
        self.current_lexeme = ""
        has_dot = False

        while True:
            char = self.stream.peek()

            if char and char.isdigit():
                self.current_lexeme += char
                self.log_step(char, "BUILDING_NUMBER", "NUMBER")
                self.stream.advance()

            elif char == ".":
                if has_dot:
                    raise LexicalError(
                        "Multiple decimal points in number",
                        self.stream.line,
                        self.stream.column
                    )
                has_dot = True
                self.current_lexeme += char
                self.log_step(char, "DECIMAL_POINT", "FLOAT")
                self.stream.advance()

            else:
                break

        token_type = "FLOAT" if has_dot else "INTEGER"
        token = Token(token_type, self.current_lexeme, self.stream.line)
        self.tokens.append(token)

        self.log_step(None, "TOKEN_GENERATED",
                      token_generated=str(token))

        self.current_state = "START"

    def handle_operator(self):

        self.current_state = "OPERATOR"
        self.current_lexeme = ""

        first_char = self.stream.advance()
        self.current_lexeme += first_char

        next_char = self.stream.peek()
        if next_char:
            potential_op = self.current_lexeme + next_char
            if potential_op in OPERATORS:
                self.current_lexeme += self.stream.advance()

        token = Token("OPERATOR", self.current_lexeme, self.stream.line)
        self.tokens.append(token)

        self.log_step(self.current_lexeme,
                      "OPERATOR_FOUND",
                      token_generated=str(token))

        self.current_state = "START"
