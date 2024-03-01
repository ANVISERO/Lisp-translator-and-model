import sys

from isa import Opcode, Term, write_code
from utility import is_num, is_word


class Translator:
    def __init__(self):
        self.IO_READ_ADDRESS = 52
        self.IO_WRITE_ADDRESS = 69
        # Массив термов
        self.terms = []
        # Текущий номер обрабатываемого токена
        self.term_number = 0
        # Массив машинного кода
        self.code = []
        # Количество незакрытых скобок
        self.deep = 0
        self.memory_map = {}
        self.stack = []
        self.jp_count = 0

    @staticmethod
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

    @staticmethod
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

    def choose_func(self):
        """Обработка текущей функции"""
        match self.terms[self.term_number].symbol:
            case "(":
                self.write_open_bracket()
            case ")":
                self.write_close_bracket()
            case "read":
                self.write_read()
            case "print":
                self.write_print()
            case "defvar":
                self.write_defvar()
            case "setq":
                self.write_setq()
            case "=":
                self.write_equally()
            case "<":
                self.write_lower()
            case "mod":
                self.write_mod()
            case "if":
                self.write_if()
            case "loop":
                self.write_loop()
            case "+" | "-" | "/" | "*":
                self.write_alu(self.terms[self.term_number].symbol)

    def write_open_bracket(self):
        self.deep += 1
        self.term_number += 1
        self.choose_func()

    def write_close_bracket(self):
        self.deep -= 1
        self.term_number += 1

    def write_read(self):
        self.code.append({"opcode": Opcode.READ.__str__(), "arg": []})
        self.deep -= 1
        self.term_number += 1

    def write_print(self):
        self.code.append(
            {
                "opcode": Opcode.DEFVAR.__str__(),
                "arg": ["$" + str(self.IO_WRITE_ADDRESS), "$" + str(self.memory_map[self.get_args()])],
            }
        )

    def write_defvar(self):
        var = self.get_args()
        self.memory_map[var] = len(self.code)
        val = self.get_args()
        if val == ")":
            val = " "
        if val == "\\n":
            val = "\n"
        self.code.append({"opcode": Opcode.DEFVAR.__str__(), "arg": ["$" + str(self.memory_map[var]), val]})

    def write_setq(self):
        val = self.get_args()
        var = self.get_args()
        if self.code[len(self.code) - 1]["opcode"] != Opcode.READ.__str__():
            if var != ")":
                self.code.append(
                    {
                        "opcode": Opcode.DEFVAR.__str__(),
                        "arg": ["$" + str(self.memory_map[val]), "$" + str(self.memory_map[var])],
                    }
                )
            else:
                self.code.append({"opcode": Opcode.SETQ.__str__(), "arg": ["$" + str(self.memory_map[val])]})
        else:
            self.code.pop()
            self.code.append(
                {
                    "opcode": Opcode.DEFVAR.__str__(),
                    "arg": ["$" + str(self.memory_map[val]), "$" + str(self.IO_READ_ADDRESS)],
                }
            )

    def write_equally(self):
        self.get_args()
        self.code.append({"opcode": Opcode.EQ.__str__(), "arg": ["$" + str(self.get_args())]})
        self.stack.append(len(self.code) - 1)
        self.term_number += 1

    def write_lower(self):
        val = self.get_args()
        self.code.append(
            {
                "opcode": Opcode.MINUS.__str__(),
                "arg": ["$" + str(self.memory_map[val]), "$" + str(self.memory_map[self.get_args()])],
            }
        )
        self.code.append({"opcode": Opcode.JL.__str__(), "arg": [0]})
        self.stack.append(len(self.code) - 1)
        self.term_number += 1

    def write_mod(self):
        arg1 = self.memory_map[self.get_args()]
        self.code.append({"opcode": Opcode.MOD.__str__(), "arg": ["$" + str(arg1), self.get_args()]})
        self.term_number += 1
        self.deep -= 1

    def write_if(self):
        if_cur_deep = self.deep
        self.term_number += 1
        while if_cur_deep <= self.deep:
            self.choose_func()
            self.term_number += 1
            if if_cur_deep == self.deep:
                break
        jl_index = self.stack.pop()
        cond = self.code[jl_index]
        self.code[jl_index] = {"opcode": cond["opcode"], "arg": ["$" + str(len(self.code))]}
        self.term_number -= 1

    def write_loop(self):
        self.stack.append(len(self.code))
        cur_deep = self.deep
        self.term_number += 1
        while cur_deep <= self.deep:
            self.choose_func()
            if cur_deep == self.deep:
                break
            self.term_number += 1
        if self.code[len(self.code) - 2]["opcode"] == "mov":
            self.choose_func()
        cond_index = self.stack.pop()
        jp_begin = self.stack.pop()
        com = self.code[cond_index]["opcode"]
        self.code[cond_index] = {"opcode": com, "arg": ["$" + str(len(self.code) + 1)]}
        self.code.append({"opcode": Opcode.JP.__str__(), "arg": ["$" + str(jp_begin)]})
        self.term_number -= 1

    def write_alu(self, operation):
        arg = []
        while self.terms[self.term_number + 1].symbol != ")":
            arg.append("$" + str(self.memory_map[self.get_args()]))
        self.code.append({"opcode": self.symbol2opcode(operation).__str__(), "arg": arg})
        self.term_number += 1
        self.deep -= 1

    def get_args(self):
        """Получение аргументов для функции"""
        self.term_number += 1
        if self.terms[self.term_number].symbol == "(":
            self.term_number += 1
            self.deep += 1
            self.choose_func()
        elif is_num(self.terms[self.term_number].symbol):
            return int(self.terms[self.term_number].symbol)
        return self.terms[self.term_number].symbol

    def text2terms(self, text):
        """Трансляция текста в последовательность операторов языка (токенов)."""
        for line in text.split("\n"):
            for pos, word in enumerate(line.split(), 1):
                if (word in self.symbols()) or (is_num(word) == 1) or (is_word(word) == 1):
                    self.terms.append(Term(pos, word))

        # Количество незакрытых скобок
        deep = 0
        for term in self.terms:
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
    translator = Translator()
    translator.text2terms(text)

    while translator.term_number < len(translator.terms):
        if translator.terms[translator.term_number].symbol == "(":
            translator.deep += 1
            translator.choose_func()
            translator.term_number += 1
        elif translator.terms[translator.term_number].symbol == ")":
            translator.deep -= 1
            translator.term_number += 1
    translator.code.append({"opcode": Opcode.HALT.__str__()})

    return translator.code


def main(source_file: str, target_file: str):
    with open(source_file, encoding="utf-8") as file:
        source_file = file.read()
        final_code = translate(source_file)
        print("source LoC:", len(source_file.split("\n")), "code instr:", len(final_code))
        write_code(target_file, final_code)


if __name__ == "__main__":
    assert len(sys.argv) == 3, "Wrong arguments: translator.py <input_file> <target_file>"
    _, source, target = sys.argv
    main(source, target)
