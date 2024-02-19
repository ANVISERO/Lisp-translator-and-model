import re


def is_word(word):
    """Проверка на то, что аргумент слово"""
    if re.search(r'\w+', word):
        return 1
    return 0


def is_num(word):
    """Проверка на то, что аргумент число"""
    try:
        int(word)
        return 1
    except ValueError:
        return 0
