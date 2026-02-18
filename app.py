from flask import Flask, render_template, request, jsonify
from lexer_engine import Lexer, LexicalError

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    code = request.json["code"]

    try:
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        return jsonify({
            "success": True,
            "tokens": [str(t) for t in tokens],
            "steps": lexer.steps,
            "symbol_table": lexer.symbol_table
        })

    except LexicalError as e:
        return jsonify({
            "success": False,
            "error": e.message,
            "line": e.line,
            "column": e.column
        })

if __name__ == "__main__":
    app.run(debug=True)
