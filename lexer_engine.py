# ============================
# LEXICAL ERROR CLASS
# ============================

class LexicalError(Exception):
    def __init__(self, message, line, column=None):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"Lexical Error: {message} at line {line}")

# ============================
# TOKEN CLASS
# ============================

class Token:
    def __init__(self, token_type, value, line, column=0):
        self.type = token_type
        self.value = value
        self.line = line
        self.column = column
    
    def __str__(self):
        return f"<{self.type}, '{self.value}', line {self.line}>"
    
    def __repr__(self):
        return self.__str__()

# ============================
# CHARACTER STREAM CLASS
# ============================

class CharStream:
    def __init__(self, text):
        self.text = text
        self.position = 0
        self.line = 1
        self.column = 1
    
    def get_char(self):
        if self.position >= len(self.text):
            return None
        
        char = self.text[self.position]
        self.position += 1
        
        if char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        
        return char
    
    def peek_char(self):
        if self.position >= len(self.text):
            return None
        return self.text[self.position]
    
    def get_position(self):
        return self.line, self.column

# ============================
# LEXER CLASS
# ============================

class Lexer:
    def __init__(self, text):
        self.stream = CharStream(text)
        self.tokens = []
        self.steps = []
        self.symbol_table = {}
        self.keywords = {'int', 'float', 'char', 'double', 'if', 'else', 'while', 'for', 'return'}
        self.operators = {'+', '-', '*', '/', '=', '==', '!=', '<', '>', '<=', '>='}
        self.delimiters = {';', ',', '(', ')', '{', '}'}
        self.current_lexeme = ""
        self.current_state = "START"
    
    def get_next_token(self):
        self.current_lexeme = ""
        self.current_state = "START"
        
        char = self.stream.get_char()
        
        while char is not None:
            # Log character processing for live execution
            self.log_step(f"Processing character: '{char}'", char=char, lexeme=self.current_lexeme)
            
            if char.isspace():
                self.current_state = "WHITESPACE"
                self.log_step(f"Skipping whitespace", char=char, lexeme=self.current_lexeme)
                char = self.stream.get_char()
                continue
            
            if char.isalpha():
                self.current_state = "BUILDING_IDENTIFIER"
                return self._read_identifier(char)
            elif char.isdigit():
                self.current_state = "BUILDING_NUMBER"
                return self._read_number(char)
            elif char == '"':
                self.current_state = "BUILDING_STRING"
                return self._read_string(char)
            elif char in self.operators:
                self.current_state = "OPERATOR"
                return self._read_operator(char)
            elif char in self.delimiters:
                self.current_state = "DELIMITER"
                return self._read_delimiter(char)
            else:
                line, column = self.stream.get_position()
                raise LexicalError(f"Unexpected character: '{char}'", line, column)
        
        return Token("EOF", "", self.stream.line, self.stream.column)
    
    def _read_identifier(self, first_char):
        self.current_lexeme = first_char
        self.current_state = "IDENTIFIER"
        char = self.stream.peek_char()
        
        while char is not None and (char.isalnum() or char == '_'):
            self.current_lexeme += self.stream.get_char()
            char = self.stream.peek_char()
            self.log_step(f"Building identifier: '{self.current_lexeme}'", lexeme=self.current_lexeme)
        
        line, column = self.stream.get_position()
        
        if self.current_lexeme in self.keywords:
            token_type = "KEYWORD"
            self.current_state = "KEYWORD"
            self.log_step(f"Found keyword: {self.current_lexeme}", lexeme=self.current_lexeme)
        else:
            token_type = "IDENTIFIER"
            self.symbol_table[self.current_lexeme] = {'type': 'variable', 'line': line}
            self.log_step(f"Found identifier: {self.current_lexeme}", lexeme=self.current_lexeme)
        
        token = Token(token_type, self.current_lexeme, line, column)
        self.log_step(f"Token generated: {token}", lexeme=self.current_lexeme)
        return token
    
    def _read_number(self, first_char):
        self.current_lexeme = first_char
        self.current_state = "NUMBER"
        has_decimal = False
        char = self.stream.peek_char()
        
        while char is not None and (char.isdigit() or (char == '.' and not has_decimal)):
            if char == '.':
                has_decimal = True
                self.current_state = "FLOAT"
            self.current_lexeme += self.stream.get_char()
            char = self.stream.peek_char()
            self.log_step(f"Building number: '{self.current_lexeme}'", lexeme=self.current_lexeme)
        
        line, column = self.stream.get_position()
        token_type = "FLOAT" if has_decimal else "INTEGER"
        self.log_step(f"Found number: {self.current_lexeme}", lexeme=self.current_lexeme)
        
        token = Token(token_type, self.current_lexeme, line, column)
        self.log_step(f"Token generated: {token}", lexeme=self.current_lexeme)
        return token
    
    def _read_string(self, first_char):
        self.current_lexeme = ""
        self.current_state = "STRING"
        char = self.stream.get_char()
        
        while char is not None and char != '"':
            self.current_lexeme += char
            self.log_step(f"Building string: '{self.current_lexeme}'", lexeme=self.current_lexeme)
            if char == '\n':
                line, column = self.stream.get_position()
                raise LexicalError("Unterminated string", line, column)
            char = self.stream.get_char()
        
        if char is None:
            line, column = self.stream.get_position()
            raise LexicalError("Unterminated string", line, column)
        
        line, column = self.stream.get_position()
        self.log_step(f"Found string: {self.current_lexeme}", lexeme=self.current_lexeme)
        
        token = Token("STRING", self.current_lexeme, line, column)
        self.log_step(f"Token generated: {token}", lexeme=self.current_lexeme)
        return token
    
    def _read_operator(self, first_char):
        line, column = self.stream.get_position()
        self.current_state = "OPERATOR"
        
        # Check for multi-character operators
        next_char = self.stream.peek_char()
        two_char_op = first_char + (next_char or '')
        
        if two_char_op in {'==', '!=', '<=', '>='}:
            self.stream.get_char()  # Consume the second character
            self.current_lexeme = two_char_op
            self.log_step(f"Found operator: {two_char_op}", lexeme=two_char_op)
            token = Token("OPERATOR", two_char_op, line, column)
            self.log_step(f"Token generated: {token}", lexeme=two_char_op)
            return token
        
        self.current_lexeme = first_char
        self.log_step(f"Found operator: {first_char}", lexeme=first_char)
        token = Token("OPERATOR", first_char, line, column)
        self.log_step(f"Token generated: {token}", lexeme=first_char)
        return token
    
    def _read_delimiter(self, first_char):
        line, column = self.stream.get_position()
        self.current_state = "DELIMITER"
        self.current_lexeme = first_char
        self.log_step(f"Found delimiter: {first_char}", lexeme=first_char)
        token = Token("DELIMITER", first_char, line, column)
        self.log_step(f"Token generated: {token}", lexeme=first_char)
        return token
    
    def log_step(self, message, action='TOKEN_GENERATED', char=None, lexeme=None):
        line, column = self.stream.get_position()
        
        step = {
            'action': action,
            'message': message,
            'line': line,
            'column': column,
            'current_state': self.current_state,
            'current_lexeme': self.current_lexeme,
            'symbol_table_snapshot': self.symbol_table.copy()  # Include current symbol table
        }
        
        # Add character info for live execution
        if char is not None:
            step['char'] = char
        
        # Add token info when generated
        if action == 'TOKEN_GENERATED' and hasattr(self, '_last_token'):
            step['token_generated'] = str(self._last_token)
        
        self.steps.append(step)
    
    def tokenize(self):
        self.tokens = []
        token = self.get_next_token()
        
        while token.type != "EOF":
            self.tokens.append(token)
            self._last_token = token  # Store for logging
            token = self.get_next_token()
        
        return self.tokens
