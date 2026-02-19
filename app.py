from flask import Flask, render_template, jsonify, request
from lexer_engine import Lexer, LexicalError
from parser_engine import Parser, SyntaxError

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        code = data.get('code', '')
        
        # Lexical analysis
        lexer = Lexer(code)
        tokens = []
        steps = []
        
        while True:
            token = lexer.get_next_token()
            if token.type == "EOF":
                break
            tokens.append(token)
        
        # Get lexer steps and symbol table
        steps = lexer.steps
        symbol_table = lexer.symbol_table
        
        # Debug: Print what we're sending
        print(f"DEBUG: Steps being sent: {steps[:3]}")  # Print first 3 steps
        print(f"DEBUG: Final symbol table: {symbol_table}")
        print(f"DEBUG: Number of symbols: {len(symbol_table)}")
        
        # Syntax analysis
        parser = Parser(tokens)
        ast = parser.parse()
        parse_steps = parser.parse_steps
        
        return jsonify({
            'success': True,
            'tokens': [{'type': t.type, 'value': t.value, 'line': t.line} for t in tokens],
            'steps': steps,
            'parse_steps': parse_steps,
            'ast': parser.ast_to_dict(ast)
        })
        
    except LexicalError as e:
        return jsonify({
            'success': False,
            'error_type': 'lexical',
            'error': str(e),
            'line': e.line,
            'column': getattr(e, 'column', 0)
        })
    
    except SyntaxError as e:
        return jsonify({
            'success': False,
            'error_type': 'syntax',
            'error': e.message,
            'line': e.line,
            'expected': getattr(e, 'expected', None),
            'found': getattr(e, 'found', None)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error_type': 'internal',
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
