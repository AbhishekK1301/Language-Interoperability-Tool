import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import re

# ------- Tokenizer -------
def tokenize(code):
    token_spec = [
        ('DEF',      r'\bdef\b'),
        ('PRINT',    r'\bprint\b'),
        ('STRING',   r'"[^"]*"'),
        ('NUMBER',   r'\d+'),
        ('ASSIGN',   r'='),
        ('LPAREN',   r'\('),
        ('RPAREN',   r'\)'),
        ('COLON',    r':'),
        ('COMMA',    r','),
        ('PLUS',     r'\+'),
        ('ID',       r'[A-Za-z_]\w*'),
        ('NEWLINE',  r'\n'),
        ('SKIP',     r'[ \t]+'),
        ('MISMATCH', r'.'),
    ]
    tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_spec)
    tokens = []
    for mo in re.finditer(tok_regex, code):
        kind = mo.lastgroup
        value = mo.group()
        if kind == 'SKIP' or kind == 'NEWLINE':
            continue
        elif kind == 'MISMATCH':
            raise RuntimeError(f'Unexpected character: {value}')
        tokens.append((kind, value))
    return tokens

# ------- Parser -------
def parse_tokens(tokens):
    i = 0
    ast = []

    def match(expected_type):
        nonlocal i
        if i < len(tokens) and tokens[i][0] == expected_type:
            val = tokens[i][1]
            i += 1
            return val
        else:
            raise SyntaxError(f"Expected {expected_type}, got {tokens[i] if i < len(tokens) else 'EOF'}")

    while i < len(tokens):
        if tokens[i][0] == 'DEF':
            match('DEF')
            func_name = match('ID')
            match('LPAREN')
            param = match('ID')
            match('RPAREN')
            match('COLON')
            body = []

            if tokens[i][0] == 'PRINT':
                match('PRINT')
                match('LPAREN')
                left = match('STRING')
                match('PLUS')
                right = match('ID')
                match('RPAREN')
                body.append({'type': 'print', 'left': left, 'right': right})
            ast.append({'type': 'function', 'name': func_name, 'param': param, 'body': body})
        elif tokens[i][0] == 'ID' and i + 1 < len(tokens) and tokens[i+1][0] == 'LPAREN':
            func_name = match('ID')
            match('LPAREN')
            arg = match('STRING')
            match('RPAREN')
            ast.append({'type': 'call', 'name': func_name, 'arg': arg})
        else:
            raise SyntaxError("Unsupported statement.")
    return ast

# ------- Intermediate Code Generator -------
def generate_ir(ast_list):
    ir_lines = []
    for node in ast_list:
        if node['type'] == 'function':
            ir_lines.append(f"func {node['name']}({node['param']})")
            for stmt in node['body']:
                if stmt['type'] == 'print':
                    temp_var = "t1"
                    ir_lines.append(f'{temp_var} = {stmt["left"]} + {stmt["right"]}')
                    ir_lines.append(f'print {temp_var}')
            ir_lines.append('endfunc')
        elif node['type'] == 'call':
            ir_lines.append(f'call {node["name"]}({node["arg"]})')
    return '\n'.join(ir_lines)

# ------- C++ Code Generator -------
def generate_cpp(ast_list):
    cpp_lines = [
        '#include <iostream>',
        '#include <string>',
        'using namespace std;',
        ''
    ]
    main_added = False
    for node in ast_list:
        if node['type'] == 'function':
            cpp_lines.append(f'void {node["name"]}(string {node["param"]}) {{')
            for stmt in node['body']:
                if stmt['type'] == 'print':
                    cpp_lines.append(f'    cout << {stmt["left"]} + {stmt["right"]} << endl;')
            cpp_lines.append('}')
        elif node['type'] == 'call':
            if not main_added:
                cpp_lines.append('\nint main() {')
                main_added = True
            cpp_lines.append(f'    {node["name"]}({node["arg"]});')
    if main_added:
        cpp_lines.append('    return 0;')
        cpp_lines.append('}')
    return '\n'.join(cpp_lines)

# ------- GUI Action -------
def translate_code():
    input_code = input_text.get("1.0", tk.END)
    try:
        tokens = tokenize(input_code)
        ast = parse_tokens(tokens)
        ir_code = generate_ir(ast)
        cpp_code = generate_cpp(ast)

        token_output.delete("1.0", tk.END)
        for t in tokens:
            token_output.insert(tk.END, f"{t}\n")

        ast_output.delete("1.0", tk.END)
        ast_output.insert(tk.END, f"{ast}")

        ir_output.delete("1.0", tk.END)
        ir_output.insert(tk.END, ir_code)

        cpp_output.delete("1.0", tk.END)
        cpp_output.insert(tk.END, cpp_code)

    except Exception as e:
        messagebox.showerror("Translation Error", str(e))

# ------- GUI Layout -------
root = tk.Tk()
root.title("Python to C++ Translator")
root.geometry("1000x800")
root.configure(bg="#f0f4f7")

style = ttk.Style()
style.configure('TButton', font=('Arial', 12), padding=10)

title_label = tk.Label(root, text="🔁 Python to C++ Translator", font=("Helvetica", 18, "bold"), bg="#f0f4f7", fg="#333")
title_label.pack(pady=10)

# Input
input_label = tk.Label(root, text="📝 Enter Python Code:", font=("Arial", 12, "bold"), bg="#f0f4f7")
input_label.pack(anchor='w', padx=10)
input_text = scrolledtext.ScrolledText(root, height=8, font=("Courier", 11), bg="white")
input_text.pack(fill='x', padx=10)

translate_btn = ttk.Button(root, text="Translate", command=translate_code)
translate_btn.pack(pady=10)

# Tokens
token_label = tk.Label(root, text="🔹 Tokens:", font=("Arial", 11, "bold"), bg="#f0f4f7")
token_label.pack(anchor='w', padx=10)
token_output = scrolledtext.ScrolledText(root, height=6, font=("Courier", 10), bg="#e9f5ff")
token_output.pack(fill='x', padx=10)

# AST
ast_label = tk.Label(root, text="🔸 AST:", font=("Arial", 11, "bold"), bg="#f0f4f7")
ast_label.pack(anchor='w', padx=10)
ast_output = scrolledtext.ScrolledText(root, height=5, font=("Courier", 10), bg="#fdf7e3")
ast_output.pack(fill='x', padx=10)

# Intermediate Code
ir_label = tk.Label(root, text="🛠️ Intermediate Code:", font=("Arial", 11, "bold"), bg="#f0f4f7")
ir_label.pack(anchor='w', padx=10)
ir_output = scrolledtext.ScrolledText(root, height=6, font=("Courier", 10), bg="#f0eaff")
ir_output.pack(fill='x', padx=10)

# C++ Code
cpp_label = tk.Label(root, text="💡 Generated C++ Code:", font=("Arial", 11, "bold"), bg="#f0f4f7")
cpp_label.pack(anchor='w', padx=10)
cpp_output = scrolledtext.ScrolledText(root, height=10, font=("Courier", 10), bg="#e2ffe5")
cpp_output.pack(fill='x', padx=10, pady=(0, 20))

root.mainloop()