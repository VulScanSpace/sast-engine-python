class SValuePattern:
    def __init__(self):
        self.value = ''
        self.type = ''
        self.line = 0
        self.end_line = 0


class SField:
    def __init__(self):
        self.expr = ''
        self.name = ''
        self.value_pattern = dict()

    def __str__(self) -> str:
        return self.expr
