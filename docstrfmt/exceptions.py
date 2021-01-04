from typing import List


class DocstrfmtError(Exception):
    """Base exception class for docstrfmt"""


class InvalidRstError(ValueError):
    def __init__(self, file, level, line, message):
        self.file = file
        self.level = level

        self.line = line
        self.message = message

    @property
    def error_message(self) -> str:
        return f'{self.level}: File "{self.file}"{f", line {self.line}" if self.line else ""}:\n{self.message}'

    def __str__(self):
        return self.error_message


class InvalidRstErrors(DocstrfmtError):
    def __init__(self, errors: List[InvalidRstError]):
        self.errors = errors

    def __str__(self):
        return "\n".join([str(error) for error in self.errors])
