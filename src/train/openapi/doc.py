from collections import defaultdict
from inspect import signature
from pathlib import Path
from string import Formatter
from typing import TYPE_CHECKING, Union, get_args, get_origin

from blacksheep import Application
from msgspec.json import schema_components
from msgspec.yaml import encode

from .docstring_parser import parse_docstring

if TYPE_CHECKING:
    from collections.abc import Callable


async def build_docs(app: Application) -> None:  # noqa: C901, PLR0915
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
            func_doc = parse_docstring(handler.__doc__ or "")
            responses: tuple[Response, ...]

            if get_origin(sig.return_annotation) is Union:
                responses = get_args(sig.return_annotation)
            else:
                responses = (sig.return_annotation,)

            if not all(get_origin(res) is Response for res in responses):
                continue

            pattern = route.pattern.decode("utf-8")
            path = paths[pattern][method.decode("utf-8").lower()] = {
                "description": func_doc["summary"],
                "parameters": [],
            }
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

    def clean(s: dict) -> dict:
        """Clean up stuff ig."""
        t = {}
        for k, v in s.items():
            r = v
            if isinstance(r, dict):
                r = clean(r)
            elif isinstance(r, list) and r and isinstance(r[0], dict):
                r = [clean(x) for x in r]

            if r in ("", [], {}):
                continue

            t[k] = r

        return t

    (Path.cwd() / "static" / "openapi.yaml").write_bytes(encode(clean(openapi)))


def bind_app(app: Application) -> None:
    app.on_start += build_docs
