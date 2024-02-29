import sys

from isa import Opcode, Term, write_code
from utility import is_num, is_word

# Массив термов
terms = []

# Текущий номер обрабатываемого токена
term_number = 0

# Массив машинного кода
code = []

# Количество незакрытых скобок
deep = 0

# Словарь
memory_map = {}
stack = []

jp_count = 0

i = 0

IO_READ_ADDRESS = 52
IO_WRITE_ADDRESS = 69


def symbols():
    """Полное множество символов языка lisp."""
    return {
        "(",
        ")",
        "read",
        "print",
        "defvar",
        "setq",
        "=",
        "<",
        "mod",
        "if",
        "loop",
        "+",
        "-",
        "*",
        "/",
    }


def symbol2opcode(symbol):
    """Отображение операторов исходного кода в коды операций."""
    return {
        "read": Opcode.READ,
        "print": Opcode.PRINT,
        "defvar": Opcode.DEFVAR,
        "setq": Opcode.SETQ,
        "=": Opcode.EQ,
        "<": Opcode.JL,
        "mod": Opcode.MOD,
        "if": Opcode.IF,
        "loop": Opcode.LOOP,
        "+": Opcode.PLUS,
        "-": Opcode.MINUS,
        "*": Opcode.MUL,
        "/": Opcode.DIV,
    }.get(symbol)


def choose_func():
    """Обработка текущей функции"""
    global terms, term_number, code, memory_map, i
    i += 1
    print(code)
    print(stack)
    match terms[term_number].symbol:
        case "(":
            write_open_bracket()
        case ")":
            write_close_bracket()
        case "read":
            write_read()
        case "print":
            write_print()
        case "defvar":
            write_defvar()
        case "setq":
            write_setq()
        case "=":
            write_equally()
        case "<":
            write_lower()
        case "mod":
            write_mod()
        case "if":
            write_if()
        case "loop":
            write_loop()
        case "+" | "-" | "/" | "*":
            write_alu(terms[term_number].symbol)


def write_open_bracket():
    global deep, term_number
    deep += 1
    term_number += 1
    choose_func()


def write_close_bracket():
    global deep, term_number
    deep -= 1
    term_number += 1


def write_read():
    global deep, term_number, code
    if code[len(code) - 1]["opcode"] == "setq":
        code.pop()
    code.append({"opcode": Opcode.READ.__str__(), "arg": []})
    deep -= 1
    term_number += 1


def write_print():
    global code, memory_map
    code.append({"opcode": Opcode.DEFVAR.__str__(), "arg": ["$" + str(IO_WRITE_ADDRESS),
                                                            "$" + str(memory_map[get_args()])]})


def write_defvar():
    global code, memory_map
    var = get_args()
    memory_map[var] = len(code)
    val = get_args()
    if val == ")":
        val = " "
    if val == "\\n":
        val = "\n"
    code.append({"opcode": Opcode.DEFVAR.__str__(), "arg": ["$" + str(memory_map[var]), val]})


def write_setq():
    global code, memory_map, IO_READ_ADDRESS
    val = get_args()
    var = get_args()
    if code[len(code) - 1]["opcode"] != Opcode.READ.__str__():
        if var != ")":
            code.append({"opcode": Opcode.DEFVAR.__str__(), "arg": ["$" + str(memory_map[val]),
                                                                    "$" + str(memory_map[var])]})
        else:
            code.append({"opcode": Opcode.SETQ.__str__(), "arg": ["$" + str(memory_map[val])]})
    else:
        code.pop()
        code.append(
            {"opcode": Opcode.DEFVAR.__str__(), "arg": ["$" + str(memory_map[val]), "$" + str(IO_READ_ADDRESS)]}
        )


def write_format():
    global code, memory_map
    get_args()
    code.append(
        {"opcode": Opcode.DEFVAR.__str__(), "arg": ["$" + str(IO_WRITE_ADDRESS), "$" + str(memory_map[get_args()])]}
    )


def write_equally():
    global term_number, code, stack
    get_args()
    code.append({"opcode": Opcode.EQ.__str__(), "arg": ["$" + str(get_args())]})
    stack.append(len(code) - 1)
    term_number += 1


def write_lower():
    global term_number, code, stack
    val = get_args()
    code.append({"opcode": Opcode.MINUS.__str__(), "arg": ["$" + str(memory_map[val]),
                                                           "$" + str(memory_map[get_args()])]})
    code.append({"opcode": Opcode.JL.__str__(), "arg": [0]})
    stack.append(len(code) - 1)
    term_number += 1


def write_mod():
    global term_number, deep
    arg1 = memory_map[get_args()]
    code.append({"opcode": Opcode.MOD.__str__(), "arg": ["$" + str(arg1), get_args()]})
    term_number += 1
    deep -= 1


def write_cond():
    global term_number, deep, code, jp_count
    idx = 0
    term_number += 1
    cur_deep = deep
    while deep >= cur_deep:
        choose_func()
        if deep == cur_deep:
            idx = stack.pop()
            begin = code[idx]
            begin["arg"][0] = len(code) + 1
            code[idx] = begin
            code.append({"opcode": Opcode.JP.__str__(), "arg": [0]})
            stack.append(len(code))
            term_number += 1
            jp_count += 1
    command = code[idx]
    command["arg"][0] = len(code) - 1
    code[idx] = command


def write_if():
    global term_number, code, stack, deep
    if_cur_deep = deep
    term_number += 1
    while if_cur_deep <= deep:
        choose_func()
        term_number += 1
        if if_cur_deep == deep:
            break
    print("if_cur_deep: " + str(if_cur_deep))
    print("deep: " + str(deep))
    print("term_number: " + str(term_number))
    jl_index = stack.pop()
    cond = code[jl_index]
    code[jl_index] = {"opcode": cond["opcode"], "arg": ["$" + str(len(code))]}
    term_number -= 1


def write_loop():
    global term_number, code, stack, deep
    stack.append(len(code))
    cur_deep = deep
    term_number += 1
    while cur_deep <= deep:
        choose_func()
        print("Before" + str(code))
        print("Before" + str(stack))
        if cur_deep == deep:
            break
        term_number += 1
    print("cur_deep: " + str(cur_deep))
    print("deep: " + str(deep))
    print("term_number: " + str(term_number))
    if code[len(code) - 2]["opcode"] == 'mov':
        print("wwwwwwwwwwwwwwwwwwwwwwww")
        choose_func()
    print("after wwwwwwwwwwwwwwwwwwwwwwww")
    cond_index = stack.pop()
    jp_begin = stack.pop()
    cond = code[cond_index]
    code[cond_index] = {"opcode": cond["opcode"], "arg": ["$" + str(len(code) + 1)]}
    code.append({"opcode": Opcode.JP.__str__(), "arg": ["$" + str(jp_begin)]})
    print("After loop: " + str(code))
    term_number -= 1


def write_alu(operation):
    global term_number, deep
    arg = []
    while terms[term_number + 1].symbol != ")":
        arg.append("$" + str(memory_map[get_args()]))
    code.append({"opcode": symbol2opcode(operation).__str__(), "arg": arg})
    term_number += 1
    deep -= 1


def get_args():
    """Получение аргументов для функции"""
    global term_number, deep
    term_number += 1
    if terms[term_number].symbol == "(":
        term_number += 1
        deep += 1
        choose_func()
    elif is_num(terms[term_number].symbol):
        return int(terms[term_number].symbol)
    return terms[term_number].symbol


def text2terms(text):
    """Трансляция текста в последовательность операторов языка (токенов)."""
    global terms

    for line in text.split("\n"):
        for pos, word in enumerate(line.split(), 1):
            if (word in symbols()) or (is_num(word) == 1) or (is_word(word) == 1):
                terms.append(Term(pos, word))

    # Количество незакрытых скобок
    deep = 0
    for term in terms:
        if term.symbol == "(":
            deep += 1
        if term.symbol == ")":
            deep -= 1
        assert deep >= 0, "Unbalanced brackets!"
    assert deep == 0, "Unbalanced brackets!"


def translate(text):
    """Трансляция текста программы в машинный код.
    Выполняется в два этапа:
    1. Трансляция текста в последовательность операторов языка (токенов).
    2. Генерация машинного кода.
        - Прямое отображение части операторов в машинный код.
        - Отображение операторов цикла в инструкции перехода с учётом
    вложенности и адресации инструкций.
    """

    text2terms(text)

    global term_number, deep

    while term_number < len(terms):
        print(terms[term_number].symbol)
        if terms[term_number].symbol == "(":
            deep += 1
            choose_func()
            if len(terms) == term_number:
                break
            term_number += 1
        elif terms[term_number].symbol == ")":
            deep -= 1
            term_number += 1
    code.append({"opcode": Opcode.HALT.__str__()})

    return code


def main(source, target):
    global code, deep
    with open(source, encoding="utf-8") as file:
        source = file.read()
    code = translate(source)
    print("source LoC:", len(source.split()), "code instr:", len(code))
    deep = 0
    write_code(target, code)


if __name__ == "__main__":
    assert len(sys.argv) == 3, "Wrong arguments: translator.py <input_file> <target_file>"
    _, source, target = sys.argv
    main(source, target)
