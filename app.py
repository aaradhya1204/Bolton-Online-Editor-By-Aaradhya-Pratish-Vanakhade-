from flask import Flask, request, jsonify, send_from_directory
import sys
import io
import os

# Import your Bolton language components
# Ensure these files (basic.py, strings_with_arrows.py, shell.py) are in the same directory
import basic
from strings_with_arrows import string_with_arrows # This is used by basic.Error

app = Flask(__name__)

# --- Serve static files (HTML, CSS, JS) ---
@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

# --- Endpoint to run Bolton code ---
@app.route('/run-bolton', methods=['POST'])
def run_bolton_code():
    data = request.get_json()
    code = data.get('code', '')

    # Capture print output and errors from stdout/stderr
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    redirected_output = io.StringIO()
    redirected_error = io.StringIO()
    sys.stdout = redirected_output
    sys.stderr = redirected_error

    result_output_from_interpreter = ""
    try:
        # Initialize a fresh global symbol table for each execution
        # This ensures that each run is independent unless you want persistent state
        global_symbol_table = basic.SymbolTable()
        global_symbol_table.set("NULL", basic.Number.null)
        global_symbol_table.set("TRUE", basic.Number.true)
        global_symbol_table.set("FALSE", basic.Number.false)
        global_symbol_table.set("MATH_PI", basic.Number.math_PI)
        global_symbol_table.set("PRINT", basic.BuiltInFunction.print)
        global_symbol_table.set("PRINT_RET", basic.BuiltInFunction.print_ret)
        global_symbol_table.set("INPUT", basic.BuiltInFunction.input)
        global_symbol_table.set("INPUT_INT", basic.BuiltInFunction.input_int)
        global_symbol_table.set("CLEAR", basic.BuiltInFunction.clear)
        global_symbol_table.set("IS_NUM", basic.BuiltInFunction.is_number)
        global_symbol_table.set("IS_STR", basic.BuiltInFunction.is_string)
        global_symbol_table.set("IS_LIST", basic.BuiltInFunction.is_list)
        global_symbol_table.set("IS_FUN", basic.BuiltInFunction.is_function)
        global_symbol_table.set("APPEND", basic.BuiltInFunction.append)
        global_symbol_table.set("POP", basic.BuiltInFunction.pop)
        global_symbol_table.set("EXTEND", basic.BuiltInFunction.extend)
        global_symbol_table.set("LEN", basic.BuiltInFunction.len)
        global_symbol_table.set("RUN", basic.BuiltInFunction.run) # Be cautious with 'RUN' in an online editor for security!

        # --- Your Bolton Language Execution Logic (from basic.py) ---
        # Lexing
        lexer = basic.Lexer('<stdin>', code)
        tokens, error = lexer.make_tokens()

        if error:
            result_output_from_interpreter = error.as_string()
        else:
            # Parsing
            parser = basic.Parser(tokens)
            ast = parser.parse()
            if ast.error:
                result_output_from_interpreter = ast.error.as_string()
            else:
                # Interpretation
                interpreter = basic.Interpreter()
                context = basic.Context('<program>')
                context.symbol_table = global_symbol_table # Assign the pre-populated symbol table
                
                runtime_result = interpreter.visit(ast.node, context)

                if runtime_result.error:
                    result_output_from_interpreter = runtime_result.error.as_string()
                elif runtime_result.value:
                    # Handle return values (e.g., if the program ends with an expression)
                    if runtime_result.value != basic.Number.null: # Don't print NULL unless explicitly done by PRINT
                        result_output_from_interpreter = str(runtime_result.value)

    except Exception as e:
        # Catch any unexpected Python errors in your basic.py logic
        result_output_from_interpreter = f"An internal server error occurred: {e}"
    finally:
        # Restore stdout/stderr
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        
        # Get captured output
        captured_stdout = redirected_output.getvalue()
        captured_stderr = redirected_error.getvalue()
        
        # Combine all output
        final_output_for_frontend = ""
        if captured_stdout:
            final_output_for_frontend += captured_stdout
        if captured_stderr:
            if final_output_for_frontend: final_output_for_frontend += "\n"
            final_output_for_frontend += captured_stderr
        if result_output_from_interpreter:
            if final_output_for_frontend: final_output_for_frontend += "\n"
            final_output_for_frontend += result_output_from_interpreter
        
        # If no output was captured and no interpreter result, provide a default message
        if not final_output_for_frontend.strip(): # .strip() to handle cases with only whitespace
            final_output_for_frontend = "Execution completed with no explicit output."

    return jsonify({'output': final_output_for_frontend})

if __name__ == '__main__':
    # Set host to '0.0.0.0' to be accessible from other devices on the network,
    # or '127.0.0.1' (localhost) for local access only.
    # debug=True allows for automatic reloading on code changes and provides debugger info.
    app.run(host='127.0.0.1', port=5000, debug=True)