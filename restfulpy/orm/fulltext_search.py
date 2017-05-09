from sqlalchemy.sql import func


escaping_map = str.maketrans({
    '&': r'\&',
    '%': r'\%',
    '!': r'\!',
    '^': r'\^',
    '$': r'\$',
    '*': r'\*',
    '[': r'\[',
    ']': r'\]',
    '(': r'\(',
    ')': r'\)',
    '{': r'\{',
    '}': r'\}',
    '\\': r'\\',
    '\'': '\'\''
})


def fts_escape(expression):
    return expression.translate(escaping_map)


def to_tsvector(*args):
    exp = args[0]
    for i in args[1:]:
        exp += ' ' + i
    return func.to_tsvector('english', exp)



