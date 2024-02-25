# Lisp. Транслятор и модель

- Иванов Андрей Вячеславович, P33101
- lisp | cisc | harv | hw | tick | struct | stream | mem | cstr | prob2 | [4]char
- Без усложнения.

## Язык программирования

``` ebnf
<Expression>      := "(" <Operation> ")"

<Operation> 	    := <F0>
		    |  <F1> <Argument>
		    |  <F2> <Argument> <Argument>
		    |  <F1+> <Arguments>
       		    |  <F2+> <Argument> <Arguments>
					
<Arguments>	    := <Argument>
	            |  <Argument> <Arguments>
             
<Argument>	    := <Variable>
		    |  <Number>
	            |  (<Argument>)

<F0>		    := "read"
<F1>		    := "print"
<F2>		    := "defvar" | "setq" | "dotimes" | "format" | "=" | "mod"
<F1+>		    := "cond" | "loop"
<F2+>		    := "+" | "-"| "*" | "/"
                       
<Variable>          := <letter>
	            |  <letter> <Variable>

<letter>            := "a" | "b" | ... | "z" | "A" | "B" | ... | "Z" | "_"
          
<Number>            := <digit>
	            |  <digit> <Variable>

<digit>	            := "0" | "1" | "2" | ... | "9"
                       

```

### Операции

- `+` Функция сложения, суммирует все параметры, возвращает результат
- `-` Функция вычитания, вычитает из первого параметра все остальные, возвращает результат
- `*` Функция умножения, умножает все параметры, возвращает результат
- `/` Функция деления, делит первый параметр на следующий и так далее, возвращает результат
- `mod` Данная функция принимает два аргумента, возвращает остаток от деления первого аргумента на второй
- `defvar` Функция объявления переменной, принимает на вход "имя переменной" "значение"
- `setq` Функция изменения значения существующей переменной, принимает на вход "имя переменной" "новое значение"
- `=` Функция принимает на вход два аргумента, если они не равны, то происходит переход на новый адрес. Поведение функции аналогично bne
- `cond` Аналог switch case.
- `dotimes` Функция объявления цикла
- `loop` Функция объявления бесконечного цикла
- `print` Функция печати в стандартный вывод числа
- `format` Функция печати в стандартный вывод символа 
- `read` Функция чтения из стандартного входного потока

## Организация памяти

1. Память команд. Машинное слово - `32` бит. Реализуется списком словарей, описывающих инструкции (одно слово - одна
   команда).
2. Память данных. Машинное слово - `32` бит, знаковое. Линейное адресное пространство. Реализуется списком чисел.

## Cистема команд

Особенности процессора:

- Машинное слово -- 32 бита, знаковое.
- Память данных:
    - адресуется через регистр `data_address`, значение может быть загружено только из Control Unit;
    - может быть записана:
        - из аккумулятора `AC`;
        - из ввода;
    - может быть прочитана в регистр данных `DR`
- Регистр аккумулятора: `AC`:
    - может быть записан в память;
    - используются флаги zero, neg;
- Регистр данных `DR`:
    - Используется для получения операндов из Control Unit, чтения данных из data memory, сохранения результатов ALU
    - Может хранить данные
    - Содержимое передается в ALU
- ALU
    - Производит арифметико - логические операции
    - На вход подаются данные из `DR` и data memory
    - Поддерживаемые операции:
        - add - сложение двух операндов
        - sub - вычесть из значения на левом входе значение на правом входе
        - mul - умножение двух операндов
        - div - поделить значение на левом входе значение на правом входе
        - mod - остаток от деления значения левого входа от правого входа
        - movv - подать на выход значение левого входа (Для чтения данных)
    - Результат записывается в `AC` или `DR`
- `program_counter` – счётчик команд:
    - Может быть перезаписан из Control Unit
    - Может быть инкрементирован
- Ввод/вывод осуществляется путем чтения и записи в определенные ячейки памяти

### Набор инструкций

| Syntax    | Mnemonic | Arguments          | Тактов | Comment                                                                                             |
|:----------|:---------|--------------------|:------:|-----------------------------------------------------------------------------------------------------|
| `defvar`  | movv     | addr, addr (value) |   3    | Устанавливает значение $2 по данному адресу $1                                                      |
| `setq`    | mov      | addr               |   2    | Загружаем значения из AC в $1                                                                       |
| `mod`     | mod      | addr, value        |   2    | Сохраняет в AC остаток от деления значения по адресу $1 на $2                                       |
| `=`       | bne      | addr               |   1    | Аналог if. Если AC != 0, то прыгаем на $2                                                           |
| `+`       | add      | addr, addr         |   4+   | Сложить значения, лежащие по адресам $1 $2, результат в AC                                          |
| `-`       | sub      | addr, addr         |   4+   | Вычесть из значения, лежащего по адресу $1 значение в адресе $2, результат в AC                     |
| `/`       | div      | addr, addr         |   4+   | Поделить значение, лежащее по адресу $1 на значение по адресу $2, результат в AC                    |
| `*`       | mul      | addr, addr         |   4+   | Умножить значения, лежащие по адресам $1 $2, результат в AC                                         |
| `dotimes` | loop     | addr, addr, addr   |  5/6   | Если значение по адресу $3 < значение по адресу $2, то переходим по адресу $1 и делаем инкремент $3 |
| `read`    | movv     | addr, addr         |   3    | Прочитать один символ с потока ввода                                                                |
| `print`   | movv     | addr, addr         |   3    | Вывод числа по адресу $1                                                                            |
| `format`  | movv     | addr, addr         |   3    | Вывод символа по адресу $1                                                                          |
| `loop`    | jp       | addr               |   1    | Безусловный переход по адресу $1                                                                    |
|           | halt     | 0                  |   0    | остановка                                                                                           | 

### Кодирование инструкций

- Машинный код сериализуется в список JSON.
- Одна команда функции – одна инструкция.
- Индекс списка – адрес инструкции. Используется для команд перехода.

Пример:

```json
    {
        "opcode": "add",
        "arg": [
            0,
            1
        ]
    }
```

где:

- `opcode` – строка с кодом операции;
- `arg` – список аргументов (может отсутствовать);

## Транслятор

Интерфейс командной строки: `translator.py <input_file> <target_file>`

Реализовано в модуле: [translator](translator.py)

Этапы трансляции (функция `translate`):

1. Трансформирование текста в последовательность значимых термов.
2. Проверка корректности программы (парность скобок).
3. Генерация машинного кода.

Правила генерации машинного кода:

- Для учета циклов и других конструкций считается количество открытых и закрытых скобок
- После открывающийся скобки может идти как функция так и её аргументы
- Аргументами функций могут быть переменные, числа, другие функции
- Мы двигаемся по всем значимым термам и формируем машинный код, пока не пройдемся по всем

## Модель процессора

Интерфейс командной строки: `machine.py <machine_code_file> <input_file>`

Реализовано в модуле: [machine](./machine.py).

## Data Path
![img.png](pictures/DataPath.png)

Реализован в классе `DataPath`.

- `data_memory` – однопортовая, поэтому либо читаем, либо пишем.
- `input` – вызовет остановку процесса моделирования, если буфер входных значений закончился.

Сигналы (обрабатываются за один такт, реализованы в виде методов класса):

- `latch_data_addr` – защёлкнуть значение в `data_addr`;
- `latch_acc` – защёлкнуть в аккумулятор значение с ALU;
- `latch_dr` – защелкнуть в регистр данных выбранное значение
- `output` – записать текущее значение `data memory` в вывод (обработка на python);
- `wr` – записать выбранное значение в память:
    - Из регистра `AC`
    - из ввода (обработка на python).

Флаги:
- `neg` – отражает наличие в аккумуляторе отрицательного числа
- `zero` – отражает наличие нулевого значения в аккумуляторе.

## Control Unit
![img.png](pictures/ControlUnit.png)

Реализован в классе `ControlUnit`.

- Hardwired (реализовано полностью на python).
- Моделирование на уровне инструкций.
- Трансляция инструкции в последовательность (0-6 тактов) сигналов: `decode_and_execute_instruction`.
- `step_counter` необходим для многотактовых команд:
    - в классе `ControlUnit` отсутствует, т.к. моделирование производится на уровне инструкций.

Сигнал:

- `latch_program_counter` – сигнал для обновления счётчика команд в ControlUnit.

Особенности работы модели:

- Для журнала состояний процессора используется стандартный модуль logging.
- Количество инструкций для моделирования ограничено hardcoded константой.
- Остановка моделирования осуществляется при:
    - исключении `EOFError` – если нет данных для чтения из порта ввода-вывода;
    - исключении `StopIteration` – если выполнена инструкция `halt`.
- Управление симуляцией реализовано в функции `simulate`.

## Тестирование

Тестирование выполняется при помощи golden test-ов.

Тесты для языка `lisp` реализованы в: [integration_test.py](integration_test.py).

Конфигурации:
- [cat.yml](golden%2Fcat.yml)
- [hello.yml](golden%2Fhello.yml)
- [hello_user_name.yml](golden%2Fhello_user_name.yml)

Запустить тесты: `poetry run pytest . -v`

Обновить конфигурацию golden tests:  `poetry run pytest . -v --update-goldens`

CI при помощи Github Action:

``` yaml
defaults:
  run:
    working-directory: ./python

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.11

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install poetry
          poetry install

      - name: Run tests and collect coverage
        run: |
          poetry run coverage run -m pytest .
          poetry run coverage report -m
        env:
          CI: true

  lint:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.11

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install poetry
          poetry install

      - name: Check code formatting with Ruff
        run: poetry run ruff format --check .

      - name: Run Ruff linters
        run: poetry run ruff check .
```

где:

- `poetry` -- управления зависимостями для языка программирования Python.
- `coverage` -- формирование отчёта об уровне покрытия исходного кода.
- `pytest` -- утилита для запуска тестов.
- `ruff` -- утилита для форматирования и проверки стиля кодирования.


Пример использования и журнал работы процессора на примере `cat`:

``` shell
$ cat examples/foo.txt
foo
$ cat examples/cat.lisp 
( defvar r )
( loop
    ( setq r ( read ) )
    ( format t r )
)
$ python3 translator.py examples/cat.lisp target.out
source LoC: 19 code instr: 5
$ cat target.out
[{"opcode": "movv", "arg": ["$0", " "]},
 {"opcode": "movv", "arg": ["$0", "$52"]},
 {"opcode": "movv", "arg": ["$69", "$0"]},
 {"opcode": "jp", "arg": [1]},
 {"opcode": "halt"}]
$ python3 machine.py target.out examples/foo.txt                  
DEBUG:root:{TICK: 0, PC: 0, ADDR: 0, MEM_OUT: 0, AC: 0, DR: 0} movv ['$0', ' ']
DEBUG:root:{TICK: 1, PC: 0, ADDR: 0, MEM_OUT: 0, AC: 0, DR: 0} movv ['$0', ' ']
DEBUG:root:{TICK: 2, PC: 0, ADDR: 0, MEM_OUT: 0, AC: 0, DR: 32} movv ['$0', ' ']
DEBUG:root:{TICK: 3, PC: 0, ADDR: 0, MEM_OUT: 0, AC: 32, DR: 32} movv ['$0', ' ']
DEBUG:root:input: ' '
DEBUG:root:{TICK: 4, PC: 0, ADDR: 0, MEM_OUT: 32, AC: 32, DR: 32} movv ['$0', ' ']
DEBUG:root:{TICK: 5, PC: 1, ADDR: 52, MEM_OUT: 102, AC: 32, DR: 32} movv ['$0', '$52']
DEBUG:root:{TICK: 6, PC: 1, ADDR: 52, MEM_OUT: 102, AC: 32, DR: 102} movv ['$0', '$52']
DEBUG:root:{TICK: 7, PC: 1, ADDR: 0, MEM_OUT: 32, AC: 32, DR: 102} movv ['$0', '$52']
DEBUG:root:{TICK: 8, PC: 1, ADDR: 0, MEM_OUT: 32, AC: 32, DR: 102} movv ['$0', '$52']
DEBUG:root:{TICK: 9, PC: 1, ADDR: 0, MEM_OUT: 32, AC: 102, DR: 102} movv ['$0', '$52']
DEBUG:root:input: 'f'
DEBUG:root:{TICK: 10, PC: 1, ADDR: 0, MEM_OUT: 102, AC: 102, DR: 102} movv ['$0', '$52']
DEBUG:root:{TICK: 11, PC: 2, ADDR: 0, MEM_OUT: 102, AC: 102, DR: 102} movv ['$69', '$0']
DEBUG:root:{TICK: 12, PC: 2, ADDR: 0, MEM_OUT: 102, AC: 102, DR: 102} movv ['$69', '$0']
DEBUG:root:{TICK: 13, PC: 2, ADDR: 69, MEM_OUT: 0, AC: 102, DR: 102} movv ['$69', '$0']
DEBUG:root:{TICK: 14, PC: 2, ADDR: 69, MEM_OUT: 0, AC: 102, DR: 102} movv ['$69', '$0']
DEBUG:root:{TICK: 15, PC: 2, ADDR: 69, MEM_OUT: 0, AC: 102, DR: 102} movv ['$69', '$0']
DEBUG:root:output: '' << 'f'
DEBUG:root:{TICK: 16, PC: 2, ADDR: 69, MEM_OUT: 102, AC: 102, DR: 102} movv ['$69', '$0']
DEBUG:root:{TICK: 17, PC: 3, ADDR: 69, MEM_OUT: 102, AC: 102, DR: 102} jp [1]
DEBUG:root:{TICK: 18, PC: 1, ADDR: 69, MEM_OUT: 102, AC: 102, DR: 102} movv ['$0', '$52']
DEBUG:root:{TICK: 19, PC: 1, ADDR: 53, MEM_OUT: 111, AC: 102, DR: 102} movv ['$0', '$52']
DEBUG:root:{TICK: 20, PC: 1, ADDR: 53, MEM_OUT: 111, AC: 102, DR: 111} movv ['$0', '$52']
DEBUG:root:{TICK: 21, PC: 1, ADDR: 0, MEM_OUT: 102, AC: 102, DR: 111} movv ['$0', '$52']
DEBUG:root:{TICK: 22, PC: 1, ADDR: 0, MEM_OUT: 102, AC: 102, DR: 111} movv ['$0', '$52']
DEBUG:root:{TICK: 23, PC: 1, ADDR: 0, MEM_OUT: 102, AC: 111, DR: 111} movv ['$0', '$52']
DEBUG:root:input: 'o'
DEBUG:root:{TICK: 24, PC: 1, ADDR: 0, MEM_OUT: 111, AC: 111, DR: 111} movv ['$0', '$52']
DEBUG:root:{TICK: 25, PC: 2, ADDR: 0, MEM_OUT: 111, AC: 111, DR: 111} movv ['$69', '$0']
DEBUG:root:{TICK: 26, PC: 2, ADDR: 0, MEM_OUT: 111, AC: 111, DR: 111} movv ['$69', '$0']
DEBUG:root:{TICK: 27, PC: 2, ADDR: 70, MEM_OUT: 0, AC: 111, DR: 111} movv ['$69', '$0']
DEBUG:root:{TICK: 28, PC: 2, ADDR: 70, MEM_OUT: 0, AC: 111, DR: 111} movv ['$69', '$0']
DEBUG:root:{TICK: 29, PC: 2, ADDR: 70, MEM_OUT: 0, AC: 111, DR: 111} movv ['$69', '$0']
DEBUG:root:output: 'f' << 'o'
DEBUG:root:{TICK: 30, PC: 2, ADDR: 70, MEM_OUT: 111, AC: 111, DR: 111} movv ['$69', '$0']
DEBUG:root:{TICK: 31, PC: 3, ADDR: 70, MEM_OUT: 111, AC: 111, DR: 111} jp [1]
DEBUG:root:{TICK: 32, PC: 1, ADDR: 70, MEM_OUT: 111, AC: 111, DR: 111} movv ['$0', '$52']
DEBUG:root:{TICK: 33, PC: 1, ADDR: 54, MEM_OUT: 111, AC: 111, DR: 111} movv ['$0', '$52']
DEBUG:root:{TICK: 34, PC: 1, ADDR: 54, MEM_OUT: 111, AC: 111, DR: 111} movv ['$0', '$52']
DEBUG:root:{TICK: 35, PC: 1, ADDR: 0, MEM_OUT: 111, AC: 111, DR: 111} movv ['$0', '$52']
DEBUG:root:{TICK: 36, PC: 1, ADDR: 0, MEM_OUT: 111, AC: 111, DR: 111} movv ['$0', '$52']
DEBUG:root:{TICK: 37, PC: 1, ADDR: 0, MEM_OUT: 111, AC: 111, DR: 111} movv ['$0', '$52']
DEBUG:root:input: 'o'
DEBUG:root:{TICK: 38, PC: 1, ADDR: 0, MEM_OUT: 111, AC: 111, DR: 111} movv ['$0', '$52']
DEBUG:root:{TICK: 39, PC: 2, ADDR: 0, MEM_OUT: 111, AC: 111, DR: 111} movv ['$69', '$0']
DEBUG:root:{TICK: 40, PC: 2, ADDR: 0, MEM_OUT: 111, AC: 111, DR: 111} movv ['$69', '$0']
DEBUG:root:{TICK: 41, PC: 2, ADDR: 71, MEM_OUT: 0, AC: 111, DR: 111} movv ['$69', '$0']
DEBUG:root:{TICK: 42, PC: 2, ADDR: 71, MEM_OUT: 0, AC: 111, DR: 111} movv ['$69', '$0']
DEBUG:root:{TICK: 43, PC: 2, ADDR: 71, MEM_OUT: 0, AC: 111, DR: 111} movv ['$69', '$0']
DEBUG:root:output: 'fo' << 'o'
DEBUG:root:{TICK: 44, PC: 2, ADDR: 71, MEM_OUT: 111, AC: 111, DR: 111} movv ['$69', '$0']
DEBUG:root:{TICK: 45, PC: 3, ADDR: 71, MEM_OUT: 111, AC: 111, DR: 111} jp [1]
DEBUG:root:{TICK: 46, PC: 1, ADDR: 71, MEM_OUT: 111, AC: 111, DR: 111} movv ['$0', '$52']
DEBUG:root:{TICK: 47, PC: 1, ADDR: 55, MEM_OUT: 0, AC: 111, DR: 111} movv ['$0', '$52']
DEBUG:root:{TICK: 48, PC: 1, ADDR: 55, MEM_OUT: 0, AC: 111, DR: 0} movv ['$0', '$52']
DEBUG:root:{TICK: 49, PC: 1, ADDR: 0, MEM_OUT: 111, AC: 111, DR: 0} movv ['$0', '$52']
DEBUG:root:{TICK: 50, PC: 1, ADDR: 0, MEM_OUT: 111, AC: 111, DR: 0} movv ['$0', '$52']
DEBUG:root:{TICK: 51, PC: 1, ADDR: 0, MEM_OUT: 111, AC: 0, DR: 0} movv ['$0', '$52']
DEBUG:root:input: '\x00'
DEBUG:root:{TICK: 52, PC: 1, ADDR: 0, MEM_OUT: 0, AC: 0, DR: 0} movv ['$0', '$52']
DEBUG:root:{TICK: 53, PC: 2, ADDR: 0, MEM_OUT: 0, AC: 0, DR: 0} movv ['$69', '$0']
DEBUG:root:{TICK: 54, PC: 2, ADDR: 0, MEM_OUT: 0, AC: 0, DR: 0} movv ['$69', '$0']
DEBUG:root:{TICK: 55, PC: 2, ADDR: 72, MEM_OUT: 0, AC: 0, DR: 0} movv ['$69', '$0']
DEBUG:root:{TICK: 56, PC: 2, ADDR: 72, MEM_OUT: 0, AC: 0, DR: 0} movv ['$69', '$0']
DEBUG:root:{TICK: 57, PC: 2, ADDR: 72, MEM_OUT: 0, AC: 0, DR: 0} movv ['$69', '$0']
INFO:root:input_buffer: < foo
WARNING:root:Input buffer is empty!
INFO:root:output_buffer: > 'foo'
foo
instr_counter: 11  ticks: 57
```

Пример проверки исходного кода:

``` shell
$ poetry run pytest . -v
========================================================================= test session starts =========================================================================
platform darwin -- Python 3.12.2, pytest-7.4.4, pluggy-1.4.0 -- /Users/anvisero/Desktop/ITMO/3course/1semester/Архитектура компьютера/lab3/.venv/bin/python
cachedir: .pytest_cache
rootdir: /Users/anvisero/Desktop/ITMO/3course/1semester/Архитектура компьютера/lab3
configfile: pyproject.toml
plugins: golden-0.2.2
collected 3 items                                                                                                                                                     

integration_test.py::test_translator_and_machine[golden/cat.yml] PASSED                                                                                         [ 33%]
integration_test.py::test_translator_and_machine[golden/hello.yml] PASSED                                                                                       [ 66%]
integration_test.py::test_translator_and_machine[golden/hello_user_name.yml] PASSED                                                                             [100%]

========================================================================== 3 passed in 0.04s ==========================================================================
$  poetry run ruff check .
$  lab3 git:(feature) ✗ poetry run ruff format .
5 files left unchanged
```


| ФИО                        | алг             | LoC  | code байт  | code инстр. | инстр. | такт. | вариант                                                                                   |
|----------------------------|-----------------|------|------------|-------------|--------|-------|-------------------------------------------------------------------------------------------|
| Иванов Андрей Вячеславович | cat             | 19   | -          | 5           | 11     | 57    | lisp \| cisc \| harv \| hw \| tick \| struct \| stream \| mem \| cstr \| prob2 \| [4]char |
| Иванов Андрей Вячеславович | hello           | 110  | -          | 20          | 19     | 98    | lisp \| cisc \| harv \| hw \| tick \| struct \| stream \| mem \| cstr \| prob2 \| [4]char |
| Иванов Андрей Вячеславович | hello_user_name | 1    | -          | 6           | 15     | 28    | lisp \| cisc \| harv \| hw \| tick \| struct \| stream \| mem \| cstr \| prob2 \| [4]char |