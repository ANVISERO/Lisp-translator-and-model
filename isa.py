import json
from collections import namedtuple
from enum import Enum


class Opcode(str, Enum):
    OPEN_BRACKET = "("
    CLOSE_BRACKET = ")"
    READ = "movv"
    PRINT = "movv"
    DEFVAR = "movv"
    SETQ = "mov"
    EQ = "bne"
    JL = "jl"
    MOD = "mod"
    IF = "cond"
    LOOP = "loop"
    PLUS = "add"
    MINUS = "sub"
    MUL = "mul"
    DIV = "div"
    JP = "jp"
    HALT = "halt"

    def __str__(self):
        return str(self.value)


class Term(namedtuple("Term", "pos symbol")):
    """Описание выражения из исходного текста программы.

    Сделано через класс, чтобы был docstring.
    """


def write_code(filename: str, code):
    """Записать машинный код в файл."""
    with open(filename, "w", encoding="utf-8") as file:
        buf = []
        for instr in code:
            buf.append(json.dumps(instr))
        file.write("[" + ",\n ".join(buf) + "]")


def read_code(filename):
    """Прочесть машинный код из файла."""
    with open(filename, encoding="utf-8") as file:
        code = json.loads(file.read())

    for instr in code:
        # Конвертация строки в Opcode
        instr["opcode"] = Opcode(instr["opcode"])

        # Конвертация списка term в класс Term
        if "term" in instr:
            assert len(instr["term"]) == 3
            instr["term"] = Term(instr["term"][0], instr["term"][1])

    return code
