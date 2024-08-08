from collections import defaultdict
from inspect import signature
from string import Formatter
from typing import TYPE_CHECKING, Union, get_args, get_origin

import warnings
from blacksheep import Application
from msgspec.json import schema_components

from train.utils import ENCODER

if TYPE_CHECKING:
    from collections.abc import Callable

from textwrap import dedent
from .string_parser import StringParser

def parse_docstring(handler):
    returnValue = {
        "summary": "",
        "parameters": {},
        "body": "",
        "responses": {}
    }

    sp = StringParser(dedent(handler.__doc__ if handler.__doc__ is not None else ""))
    
    returnValue["summary"] = sp.consume_until(lambda c: c == "@").strip()
    while not sp.is_done():
        sp.skip()
        type_of = sp.consume_until(lambda c: c == ":").strip()
        sp.skip()
        if type_of.startswith("param"):
            name = type_of.split()[-1]
            body = sp.consume_until(lambda c: c == "@").strip()
            returnValue["parameters"][name] = body

        elif type_of.startswith("body"):
            body = sp.consume_until(lambda c: c == "@").strip()
            returnValue["body"] = body

        elif type_of.startswith("response"):
            status = type_of.split()[-1]
            body = sp.consume_until(lambda c: c == "@").strip()
            returnValue["responses"][status] = body

    return returnValue
        

    
    


def build_docs(app: Application) -> bytes:  # noqa: C901
    from train.app import FromJSON, Response

    fmt = Formatter()

    types = []
    params = []
    idk_what_im_doing: list[dict] = []
    idk_what_im_doing_again: list[dict] = []

    paths = defaultdict(dict)
    for method, routes in app.router.routes.items():
        for route in routes:
            handler: Callable = route.handler
            sig = signature(handler)
            func_doc = parse_docstring(handler)

            responses: tuple[Response, ...]
            if get_origin(sig.return_annotation) is Union:
                responses = get_args(sig.return_annotation)
            else:
                responses = (sig.return_annotation,)

            if not all(get_origin(res) is Response for res in responses):
                continue

            pattern = route.pattern.decode("utf-8")
            path = paths[pattern][method.decode("utf-8").lower()] = {
                "description": func_doc["summary"]
            }
            path["parameters"] = []
            for schema in fmt.parse(pattern):
                param_name = schema[1]
                if param_name is None:
                    continue

                param = sig.parameters[param_name].annotation
                params.append(param)

                idk_what_im_doing_again.append({})
                path["parameters"].append(
                    {
                        "name": param_name,
                        "in": "path",
                        "required": True,
                        "schema": idk_what_im_doing_again[-1],
                        "description": func_doc["parameters"].get(param_name, ""),
                    },
                )

            path["operationId"] = handler.__name__

            path["responses"] = {}
            for response in responses:
                status, klass = get_args(response)
                status = str(get_args(status)[0])

                idk_what_im_doing.append({})
                path["responses"][status] = {
                    "description": func_doc["responses"].get(status, ""),
                    "content": {
                        "application/json": {
                            "schema": idk_what_im_doing[-1],
                        },
                    },
                }

                types.append(klass)

            for klass in sig.parameters.values():
                annotation = klass.annotation
                origin = get_origin(annotation)
                if origin is FromJSON:
                    body = get_args(annotation)[0]
                    types.append(body)

                    idk_what_im_doing.append({})
                    path["requestBody"] = {
                        "description": func_doc["body"],
                        "content": {
                            "application/json": {
                                "schema": idk_what_im_doing[-1],
                            },
                        },
                    }

    schemas, parameter_components = schema_components(
        params,
        ref_template="#/components/parameters/{name}",
    )
    for i, schema in enumerate(schemas):
        idk_what_im_doing_again[i].update(schema)

    schemas, components = schema_components(
        types,
        ref_template="#/components/schemas/{name}",
    )
    for i, schema in enumerate(schemas):
        idk_what_im_doing[i].update(schema)

    openapi = {
        "openapi": "3.1.0",
        "info": {
            "title": "FTCB API",
            "version": "0.0.0-alpha",
        },
        "paths": paths,
        "servers": [],
        "components": {"schemas": components, "parameters": parameter_components},
    }

    return ENCODER.encode(openapi)
