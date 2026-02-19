# ============================
# SYNTAX ERROR CLASS
# ============================

class SyntaxError(Exception):
    def __init__(self, message, line, expected=None, found=None):
        self.message = message
        self.line = line
        self.expected = expected
        self.found = found
        super().__init__(f"{message} at line {line}")

# ============================
# AST NODE CLASSES
# ============================

class ASTNode:
    def __init__(self, node_type, line=None):
        self.type = node_type
        self.line = line
        self.children = []
    
    def add_child(self, child):
        self.children.append(child)
    
    def __repr__(self):
        return f"{self.type}()"

class ProgramNode(ASTNode):
    def __init__(self, line=None):
        super().__init__("Program", line)
    
    def __repr__(self):
        return f"Program({len(self.children)} statements)"

class DeclarationNode(ASTNode):
    def __init__(self, var_type, var_name, line=None):
        super().__init__("Declaration", line)
        self.var_type = var_type
        self.var_name = var_name
    
    def __repr__(self):
        return f"Declaration({self.var_type} {self.var_name})"

class AssignmentNode(ASTNode):
    def __init__(self, var_name, line=None):
        super().__init__("Assignment", line)
        self.var_name = var_name
        self.add_child(IdentifierNode(var_name, line))
    
    def __repr__(self):
        return f"Assignment({self.var_name})"

class BinaryOpNode(ASTNode):
    def __init__(self, operator, left, right, line=None):
        super().__init__("BinaryOp", line)
        self.operator = operator
        self.left = left
        self.right = right
        self.add_child(left)
        self.add_child(right)
    
    def __repr__(self):
        return f"BinaryOp({self.operator})"

class NumberNode(ASTNode):
    def __init__(self, value, line=None):
        super().__init__("Number", line)
        self.value = value
    
    def __repr__(self):
        return f"Number({self.value})"

class StringNode(ASTNode):
    def __init__(self, value, line=None):
        super().__init__("String", line)
        self.value = value
    
    def __repr__(self):
        return f"String({self.value})"

class IdentifierNode(ASTNode):
    def __init__(self, name, line=None):
        super().__init__("Identifier", line)
        self.name = name
    
    def __repr__(self):
        return f"Identifier({self.name})"

class FunctionCallNode(ASTNode):
    def __init__(self, function_name, line=None):
        super().__init__("FunctionCall", line)
        self.function_name = function_name
        self.arguments = []
    
    def add_argument(self, arg):
        self.arguments.append(arg)
        self.add_child(arg)
    
    def __repr__(self):
        return f"FunctionCall({self.function_name}, {len(self.arguments)} args)"

# ============================
# PARSER CLASS
# ============================

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_token = None
        self.position = -1
        self.parse_steps = []
        self.routine_stack = []
        self.advance()
    
    def advance(self):
        self.position += 1
        if self.position < len(self.tokens):
            self.current_token = self.tokens[self.position]
        else:
            self.current_token = None
    
    def peek(self):
        if self.position + 1 < len(self.tokens):
            return self.tokens[self.position + 1]
        return None
    
    def expect(self, token_type, token_value=None):
        if not self.current_token:
            raise SyntaxError("Unexpected end of input", self.get_current_line())
        
        if self.current_token.type != token_type:
            raise SyntaxError(
                f"Expected {token_type}, got {self.current_token.type}",
                self.get_current_line(),
                expected=token_type,
                found=self.current_token.type
            )
        
        if token_value and self.current_token.value != token_value:
            raise SyntaxError(
                f"Expected '{token_value}', got '{self.current_token.value}'",
                self.get_current_line(),
                expected=token_value,
                found=self.current_token.value
            )
        
        self.log_step("CONSUME", f"Consumed: {self.current_token}")
        consumed = self.current_token
        self.advance()
        return consumed
    
    def get_current_line(self):
        return self.current_token.line if self.current_token else 0
    
    def log_step(self, action, message, node_created=None, routine=None):
        step = {
            'action': action,
            'message': message,
            'current_token': str(self.current_token) if self.current_token else None,
            'line': self.get_current_line()
        }
        
        if node_created:
            step['token_generated'] = str(node_created)
        
        if routine:
            step['routine'] = routine
            if action == "ROUTINE":
                self.routine_stack.append(routine)
            elif action in ["COMPLETE", "CREATE_NODE"]:
                if self.routine_stack and self.routine_stack[-1] == routine:
                    self.routine_stack.pop()
        
        step['stack'] = list(self.routine_stack)
        self.parse_steps.append(step)
    
    def parse(self):
        self.log_step("START", "Beginning parsing", routine="parse_program")
        program = ProgramNode()
        
        while self.current_token:
            if self.current_token.type in {"KEYWORD"} and self.current_token.value in {"int", "float", "char", "double"}:
                self.log_step("CHECK", "Found type keyword", routine="parse_declaration")
                decl_or_assign = self.parse_declaration_or_assignment()
                if decl_or_assign:
                    program.add_child(decl_or_assign)
            elif self.current_token.type == "IDENTIFIER":
                self.log_step("CHECK", "Found identifier", routine="parse_identifier_statement")
                stmt = self.parse_identifier_statement()
                if stmt:
                    program.add_child(stmt)
            else:
                raise SyntaxError(
                    f"Unexpected token {self.current_token.type}",
                    self.get_current_line()
                )
        
        self.log_step("COMPLETE", "Parsing completed successfully", program, routine="parse_program")
        return program
    
    def parse_declaration_or_assignment(self):
        self.log_step("ROUTINE", "Starting declaration/assignment", routine="parse_declaration_or_assignment")
        
        if not self.current_token:
            raise SyntaxError("Unexpected end of input", self.get_current_line())
        
        # Check if it's a type keyword (declaration)
        if self.current_token.type == "KEYWORD" and self.current_token.value in {"int", "float", "char", "double"}:
            return self.parse_declaration()
        
        # Otherwise, it's an assignment or expression
        return self.parse_assignment()
    
    def parse_declaration(self):
        self.log_step("ROUTINE", "Starting declaration", routine="parse_declaration")
        
        var_type = self.expect("KEYWORD").value
        var_name = self.expect("IDENTIFIER").value
        
        declaration = DeclarationNode(var_type, var_name, self.get_current_line())
        self.log_step("CREATE_NODE", f"Created declaration: {var_type} {var_name}", declaration)
        
        # Check for initialization
        if self.current_token and self.current_token.value == "=":
            self.expect("OPERATOR", "=")
            expr = self.parse_expression()
            declaration.add_child(expr)
        
        self.expect("DELIMITER", ";")
        self.log_step("COMPLETE", "Declaration complete", routine="parse_declaration")
        return declaration
    
    def parse_assignment(self):
        self.log_step("ROUTINE", "Starting assignment", routine="parse_assignment")
        
        var_name = self.expect("IDENTIFIER").value
        self.expect("OPERATOR", "=")
        
        expr = self.parse_expression()
        
        assignment = AssignmentNode(var_name, self.get_current_line())
        assignment.add_child(expr)
        self.log_step("CREATE_NODE", f"Created assignment: {var_name} =", assignment)
        
        self.expect("DELIMITER", ";")
        self.log_step("COMPLETE", "Assignment complete", routine="parse_assignment")
        return assignment
    
    def parse_function_call(self, function_name):
        self.log_step("ROUTINE", "Starting function call", routine="parse_function_call")
        
        function_call = FunctionCallNode(function_name, self.get_current_line())
        self.log_step("CREATE_NODE", f"Created function call: {function_name}", function_call)
        
        self.expect("DELIMITER", "(")
        
        # Parse arguments
        if self.current_token and self.current_token.value != ")":
            arg = self.parse_expression()
            function_call.add_argument(arg)
            
            while self.current_token and self.current_token.value == ",":
                self.expect("DELIMITER", ",")
                arg = self.parse_expression()
                function_call.add_argument(arg)
        
        self.expect("DELIMITER", ")")
        self.expect("DELIMITER", ";")
        
        self.log_step("COMPLETE", "Function call complete", routine="parse_function_call")
        return function_call
    
    def parse_identifier_statement(self):
        self.log_step("ROUTINE", "Starting identifier statement", routine="parse_identifier_statement")
        
        var_name = self.expect("IDENTIFIER").value
        
        # Check if it's a function call
        if self.current_token and self.current_token.value == "(":
            return self.parse_function_call(var_name)
        
        # Otherwise, it's an assignment
        self.expect("OPERATOR", "=")
        
        expr = self.parse_expression()
        
        assignment = AssignmentNode(var_name, self.get_current_line())
        assignment.add_child(expr)
        self.log_step("CREATE_NODE", f"Created assignment: {var_name} =", assignment)
        
        self.expect("DELIMITER", ";")
        self.log_step("COMPLETE", "Identifier statement complete", routine="parse_identifier_statement")
        return assignment
    
    def parse_expression(self):
        self.log_step("ROUTINE", "Starting expression parsing", routine="parse_expression")
        result = self.parse_additive_expression()
        self.log_step("COMPLETE", "Expression parsing complete", routine="parse_expression")
        return result
    
    def parse_additive_expression(self):
        self.log_step("ROUTINE", "Starting additive expression", routine="parse_additive_expression")
        result = self.parse_multiplicative_expression()
        
        while self.current_token and self.current_token.value in ('+', '-'):
            operator = self.current_token.value
            self.log_step("OPERATOR", f"Found operator: {operator}")
            self.expect("OPERATOR")
            right = self.parse_multiplicative_expression()
            result = BinaryOpNode(operator, result, right, self.get_current_line())
            self.log_step("CREATE_NODE", f"Created binary op: {operator}", result)
        
        self.log_step("COMPLETE", "Additive expression complete", routine="parse_additive_expression")
        return result
    
    def parse_multiplicative_expression(self):
        self.log_step("ROUTINE", "Starting multiplicative expression", routine="parse_multiplicative_expression")
        result = self.parse_primary_expression()
        
        while self.current_token and self.current_token.value in ('*', '/'):
            operator = self.current_token.value
            self.log_step("OPERATOR", f"Found operator: {operator}")
            self.expect("OPERATOR")
            right = self.parse_primary_expression()
            result = BinaryOpNode(operator, result, right, self.get_current_line())
            self.log_step("CREATE_NODE", f"Created binary op: {operator}", result)
        
        self.log_step("COMPLETE", "Multiplicative expression complete", routine="parse_multiplicative_expression")
        return result
    
    def parse_primary_expression(self):
        self.log_step("ROUTINE", "Starting primary expression", routine="parse_primary_expression")
        
        if self.current_token and self.current_token.type in {"NUMBER", "INTEGER", "FLOAT"}:
            value = self.current_token.value
            self.log_step("CONSUME", f"Consumed number: {value}")
            node = NumberNode(value, self.get_current_line())
            self.log_step("CREATE_NODE", f"Created number: {value}", node)
            self.advance()
            return node
        
        elif self.current_token and self.current_token.type == "STRING":
            value = self.current_token.value
            self.log_step("CONSUME", f"Consumed string: {value}")
            node = StringNode(value, self.get_current_line())
            self.log_step("CREATE_NODE", f"Created string: {value}", node)
            self.advance()
            return node
        
        elif self.current_token and self.current_token.type == "IDENTIFIER":
            name = self.current_token.value
            self.log_step("CONSUME", f"Consumed identifier: {name}")
            node = IdentifierNode(name, self.get_current_line())
            self.log_step("CREATE_NODE", f"Created identifier: {name}", node)
            self.advance()
            return node
        
        elif self.current_token and self.current_token.value == "(":
            self.expect("DELIMITER", "(")
            expr = self.parse_expression()
            self.expect("DELIMITER", ")")
            return expr
        
        else:
            raise SyntaxError(
                "Expected number, string, identifier, or '('",
                self.get_current_line()
            )
    
    def ast_to_dict(self, node):
        """Convert AST node to dictionary for JSON serialization"""
        if node is None:
            return None
        
        result = {
            'type': node.type,
            'line': node.line
        }
        
        # Add specific attributes based on node type
        if hasattr(node, 'value'):
            result['value'] = node.value
        if hasattr(node, 'name'):
            result['name'] = node.name
        if hasattr(node, 'var_name'):
            result['var_name'] = node.var_name
        if hasattr(node, 'var_type'):
            result['var_type'] = node.var_type
        if hasattr(node, 'operator'):
            result['operator'] = node.operator
        if hasattr(node, 'function_name'):
            result['function_name'] = node.function_name
        
        # Add children
        if hasattr(node, 'children') and node.children:
            result['children'] = [self.ast_to_dict(child) for child in node.children]
        elif hasattr(node, 'arguments') and node.arguments:
            result['children'] = [self.ast_to_dict(arg) for arg in node.arguments]
        
        return result
