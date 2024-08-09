from textwrap import dedent
from typing import TypedDict

from .string_parser import StringParser


class ParsedDocstring(TypedDict):
    summary: str
    parameters: dict[str, str]
    body: str
    responses: dict[str, str]


def parse_docstring(docstring: str) -> ParsedDocstring:
    sp = StringParser(dedent(docstring))
    return_value: ParsedDocstring = {
        "summary": "",
        "parameters": {},
        "responses": {},
        "body": "",
    }

    return_value["summary"] = sp.consume_until(lambda c: c == "@").strip()
    while not sp.is_done():
        sp.skip()  # skip the @ character
        type_of = sp.consume_until(lambda c: c == ":").strip()
        sp.skip()
        if type_of.startswith("param"):
            name = type_of.split()[-1]
            body = sp.consume_until(lambda c: c == "@").strip()
            return_value["parameters"][name] = body

        elif type_of.startswith("body"):
            body = sp.consume_until(lambda c: c == "@").strip()
            return_value["body"] = body

        elif type_of.startswith("response"):
            status = type_of.split()[-1]
            body = sp.consume_until(lambda c: c == "@").strip()
            return_value["responses"][status] = body

    return return_value
