"""Модель процессора, позволяющая выполнить машинный код полученный из программы
на языке lisp.

Модель включает в себя три основных компонента:

- `DataPath` -- работа с памятью данных и вводом-выводом.

- `ControlUnit` -- работа с памятью команд и их интерпретация.

"""

import logging
import sys
from math import copysign

from isa import Opcode, read_code

#  Маска для переполнения чисел
MUSK_NUMBER = 2**32 - 1


class DataPath:
    def __init__(self, data_memory_size, input_buffer_begin, output_buffer_begin, input_tokens):
        assert data_memory_size > 0, "Data_memory size should be non-zero"
        self.data_memory_size = data_memory_size
        self.data_memory = [0] * data_memory_size
        self.data_address = 0
        self.acc = 0
        self.dr = 0
        self.input_buffer_begin = input_buffer_begin
        self.output_buffer_begin = output_buffer_begin
        self.input_buffer_pointer = 0
        self.output_buffer_pointer = 0
        self.input_buffer_size = len(input_tokens)
        for index, value in enumerate(input_tokens):
            assert input_buffer_begin + index < output_buffer_begin, "input memory mapping size is out of bound"
            symbol_code = ord(value)
            assert -128 <= symbol_code <= 127, "input token is out of bound: {}".format(symbol_code)
            self.data_memory[input_buffer_begin + index] = symbol_code
        self.data_memory[input_buffer_begin + len(input_tokens)] = 0
        self.max_data_value = 2147483647
        self.min_data_value = -2147483648

    def latch_data_addr(self, new_addr):
        """Данная функция позволяет загружать новые значения (адреса) в регистр адреса"""
        assert 0 <= new_addr < self.data_memory_size, f"out of memory: {format(self.data_address)}"
        self.data_address = new_addr

    def latch_dr(self, sel, arg, op_type):
        """Защелкнуть DR = прочитать данные из памяти
        sel = 1 Считать данные из декодера инструкций
        sel = 2 Считать данные из текущего адреса памяти
        sel = 3 Защелкнуть данные с АЛУ"""
        if sel == 1:
            self.dr = arg
        elif sel == 2:
            self.dr = self.data_memory[self.data_address]
        else:
            self.dr = self.alu(op_type)

    def latch_acc(self, op_type):
        """Защелкнуть новое значение AC, новое значение приходит из ALU
        в зависимости от входного сигнала выбирается операция на ALU"""
        self.acc = self.alu(op_type)

    def alu(self, op_type):
        global MUSK_NUMBER
        cur_value = 0
        match op_type:
            case "add":
                cur_value = self.data_memory[self.data_address] + self.dr
            case "mul":
                cur_value = self.data_memory[self.data_address] * self.dr
            case "sub":
                cur_value = self.data_memory[self.data_address] - self.dr
            case "div":
                cur_value = self.data_memory[self.data_address] / self.dr
            case "mod":
                cur_value = self.data_memory[self.data_address] % self.dr
            case Opcode.DEFVAR:
                cur_value = self.dr
            case "inc":
                cur_value = self.dr + 1

        # Проверка на переполнение
        if abs(cur_value) > self.max_data_value:
            cur_value = copysign(abs(cur_value) & MUSK_NUMBER, cur_value)

        return cur_value

    def write(self):
        """Записать в текущую ячейку данные из AC"""
        if isinstance(self.acc, int):
            assert (
                self.min_data_value <= self.data_memory[self.data_address] <= self.max_data_value
            ), f"acc value is out of bound: {self.data_memory[self.data_address]}"
        if self.output_buffer_begin <= self.data_address <= self.data_memory_size:
            if self.zero():
                input_buffer = list(
                    map(
                        chr,
                        self.data_memory[
                            self.input_buffer_begin : self.input_buffer_begin + self.input_buffer_pointer - 1
                        ],
                    )
                )
                logging.info("input_buffer: < %s", ("".join(input_buffer)))
                self.output_buffer_pointer -= 1
                raise EOFError()
            logging.debug(
                "output: %s << %s",
                repr(
                    "".join(
                        list(
                            map(
                                chr,
                                self.data_memory[
                                    self.output_buffer_begin : self.output_buffer_begin + self.output_buffer_pointer - 1
                                ],
                            )
                        )
                    )
                ),
                repr(chr(self.acc)),
            )
        else:
            logging.debug("input: %s", repr(chr(self.acc)))
        self.data_memory[self.data_address] = self.acc

    def zero(self):
        """Флаг нужен для циклов и джампов"""
        return self.acc == 0

    def neg(self):
        """Флаг нужен для проверки на знак"""
        return self.acc < 0


class ControlUnit:
    def __init__(self, program, data_path):
        self.program = program
        self.program_counter = 0
        self.program_counter_max = 0
        self.data_path = data_path
        self._tick = 0
        self.current_arg = 0

    def tick(self):
        """Счётчик тактов процессора. Вызывается при переходе на следующий такт."""
        self._tick += 1
        logging.debug("%s", self)

    def get_current_arg(self):
        return self.current_arg

    def current_tick(self):
        return self._tick

    def latch_program_counter(self, sel_next):
        self.tick()
        if sel_next:
            self.program_counter += 1
        else:
            instr = self.program[self.program_counter]
            assert "arg" in instr, "internal error"
            self.program_counter = instr["arg"][0]
        if self.program_counter > self.program_counter_max:
            self.program_counter_max = self.program_counter

    def decode_and_execute_instruction(self):
        instr = self.program[self.program_counter]
        opcode = instr["opcode"]
        if (
            self.data_path.data_memory[self.data_path.output_buffer_begin + self.data_path.output_buffer_pointer - 1]
            == 10
        ):
            output_buffer = list(
                map(
                    chr,
                    self.data_path.data_memory[
                        self.data_path.output_buffer_begin : self.data_path.output_buffer_begin
                        + self.data_path.output_buffer_pointer
                        - 1
                    ],
                )
            )
            logging.info("output_buffer: > %s", repr("".join(output_buffer)))
            self.data_path.output_buffer_pointer = 0
        match opcode:
            case Opcode.HALT:
                raise StopIteration()
            case Opcode.DEFVAR | Opcode.SETQ:
                self.execute_defvar(instr, opcode)
            case Opcode.MOD:
                self.execute_mod(instr, opcode)
            case Opcode.EQ:
                self.execute_eq()
            case Opcode.PLUS | Opcode.MINUS | Opcode.MUL | Opcode.DIV:
                self.execute_alu(instr, opcode)
            case Opcode.SETQ:
                self.execute_setq(instr)
            case Opcode.JP:
                self.execute_jp()
            case Opcode.DOTIMES:
                self.execute_dotimes(instr)

    def execute_defvar(self, instr, opcode):
        if isinstance(instr["arg"][1], str):
            if instr["arg"][1][0] == "$":
                if int(instr["arg"][1][1:]) == self.data_path.input_buffer_begin:
                    self.data_path.latch_data_addr(int(instr["arg"][1][1:]) + self.data_path.input_buffer_pointer)
                    self.data_path.input_buffer_pointer += 1
                else:
                    self.data_path.latch_data_addr(int(instr["arg"][1][1:]))

                self.tick()
                self.data_path.latch_dr(2, None, None)
                self.tick()
                if int(instr["arg"][0][1:]) == self.data_path.output_buffer_begin:
                    self.data_path.latch_data_addr(int(instr["arg"][0][1:]) + self.data_path.output_buffer_pointer)
                    self.data_path.output_buffer_pointer += 1
                else:
                    self.data_path.latch_data_addr(int(instr["arg"][0][1:]))
                self.tick()
            else:
                self.data_path.latch_data_addr(int(instr["arg"][0][1:]))
                self.tick()
                self.data_path.latch_dr(1, ord(instr["arg"][1]), None)
        else:
            self.data_path.latch_data_addr(["arg"][1][0])
            self.tick()
            self.data_path.latch_dr(1, instr["arg"][1], None)

        self.tick()
        self.data_path.latch_acc(opcode)
        self.tick()
        self.data_path.write()
        self.latch_program_counter(sel_next=True)

    def execute_mod(self, instr, opcode):
        self.data_path.latch_data_addr(instr["arg"][0])
        self.data_path.latch_dr(1, instr["arg"][1], None)
        self.tick()

        self.data_path.latch_acc(opcode)
        self.tick()
        self.latch_program_counter(sel_next=True)

    def execute_eq(self):
        self.tick()
        if self.data_path.zero():
            self.latch_program_counter(sel_next=True)
        else:
            self.latch_program_counter(sel_next=False)

    def execute_alu(self, instr, opcode):
        self.data_path.latch_data_addr(instr["arg"][0])
        self.tick()

        self.data_path.latch_dr(2, None, None)
        self.tick()
        self.data_path.latch_data_addr(instr["arg"][1])
        self.tick()
        arg_counter = 2
        while arg_counter < len(instr["arg"]):
            self.data_path.latch_dr(3, None, opcode)
            self.tick()
            self.data_path.latch_data_addr(instr["arg"][arg_counter])
            arg_counter += 1
            self.tick()

        self.data_path.latch_acc(opcode)
        self.tick()
        self.latch_program_counter(sel_next=True)

    def execute_setq(self, instr):
        self.data_path.latch_data_addr(instr["arg"])
        self.tick()

        self.data_path.write()
        self.tick()
        self.latch_program_counter(sel_next=True)

    def execute_jp(self):
        self.latch_program_counter(sel_next=False)
        self.tick()

    def execute_dotimes(self, instr):
        self.data_path.latch_data_addr(instr["arg"][2])
        self.tick()

        self.data_path.latch_dr(2, None, None)
        self.tick()

        self.data_path.latch_data_addr(instr["arg"][1])
        self.tick()

        self.data_path.latch_acc(Opcode.MINUS)
        self.tick()

        if self.data_path.neg() | self.data_path.zero():
            self.latch_program_counter(sel_next=True)
            self.tick()
        else:
            self.data_path.latch_acc("inc")
            self.data_path.latch_data_addr(instr["arg"][2])
            self.tick()

            self.data_path.write()
            self.latch_program_counter(sel_next=False)
            self.tick()

    def __repr__(self):
        state = "TICK: {}, PC: {}, ADDR: {}, MEM_OUT: {}, AC: {}, DR: {}".format(
            self._tick,
            self.program_counter,
            self.data_path.data_address,
            self.data_path.data_memory[self.data_path.data_address],
            self.data_path.acc,
            self.data_path.dr,
        )

        instr = self.program[self.program_counter]
        opcode = instr["opcode"]
        arg = instr.get("arg", "")
        action = f"{opcode} {arg}"

        return f"{state} {action}"


def simulation(code, input_tokens, input_buffer_begin, output_buffer_begin, data_memory_size, limit):
    """Подготовка модели и запуск симуляции процессора.

    Длительность моделирования ограничена:

    - количеством выполненных инструкций (`limit`);

    - количеством данных ввода (`input_tokens`, если ввод используется), через
      исключение `EOFError`;

    - инструкцией `Halt`, через исключение `StopIteration`.
    """
    data_path = DataPath(data_memory_size, input_buffer_begin, output_buffer_begin, input_tokens)
    control_unit = ControlUnit(code, data_path)
    instr_counter = 0

    logging.debug("%s", control_unit)
    try:
        while True:
            assert limit > instr_counter, "too long execution, increase limit!"
            control_unit.decode_and_execute_instruction()
            instr_counter += 1
    except EOFError:
        logging.warning("Input buffer is empty!")
        control_unit.program_counter_max += 1
        control_unit.program_counter = control_unit.program_counter_max
        try:
            while True:
                assert limit > instr_counter, "too long execution, increase limit!"
                control_unit.decode_and_execute_instruction()
                instr_counter += 1
        except StopIteration:
            pass
    except StopIteration:
        pass

    if instr_counter >= limit:
        logging.warning("Limit exceeded!")

    output_buffer = list(
        map(
            chr,
            data_path.data_memory[
                data_path.output_buffer_begin : data_path.output_buffer_begin + data_path.output_buffer_pointer
            ],
        )
    )
    logging.info("output_buffer: > %s", repr("".join(output_buffer)))
    return "".join(output_buffer), instr_counter, control_unit.current_tick()


def main(code_file, input_file):
    """Функция запуска модели процессора. Параметры -- имена файлов с машинным
    кодом и с входными данными для симуляции.
    """
    code = read_code(code_file)
    with open(input_file, encoding="utf-8") as file:
        input_text = file.read()
        input_token = []
        for char in input_text:
            input_token.append(char)

    io_read_address = 52
    io_write_address = 69
    output, instr_counter, ticks = simulation(
        code,
        input_tokens=input_token,
        input_buffer_begin=io_read_address,
        output_buffer_begin=io_write_address,
        data_memory_size=100,
        limit=1000,
    )

    print("".join(output))
    print("instr_counter:", instr_counter, " ticks:", ticks)


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    assert len(sys.argv) == 3, "Wrong arguments: machine.py <code_file> <input_file>"
    _, code_file, input_file = sys.argv
    main(code_file, input_file)
