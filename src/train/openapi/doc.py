from collections import defaultdict
from inspect import signature
from pathlib import Path
from string import Formatter
from typing import TYPE_CHECKING, Any, Union, get_args, get_origin

from blacksheep import Application
from msgspec.json import schema_components
from msgspec.yaml import encode

from .docstring_parser import parse_docstring

if TYPE_CHECKING:
    from collections.abc import Callable


def unwrap_union_type(t: type) -> tuple[Any, ...]:
    """Unwrap the type if it was a union and provide results as a tuple."""
    if get_origin(t) is Union:
        return get_args(t)

    return (t,)


def clean(dirty: dict) -> dict:
    """Clean up stuff ig."""
    cleaned = {}
    for k, v in dirty.items():
        cleaned_value = v
        if isinstance(cleaned_value, dict):
            cleaned_value = clean(cleaned_value)
        elif (
            isinstance(cleaned_value, list)
            and cleaned_value
            and isinstance(cleaned_value[0], dict)
        ):
            cleaned_value = [clean(x) for x in cleaned_value]

        if cleaned_value in ("", [], {}):
            continue

        cleaned[k] = cleaned_value

    return cleaned


async def build_docs(app: Application) -> None:  # noqa: C901
    from train.app import FromJSON, Response

    fmt = Formatter()

    types = []
    params = []
    body_and_response_schemas: list[dict] = []
    parameter_schemas: list[dict] = []

    paths = defaultdict(dict)
    for method, routes in app.router.routes.items():
        for route in routes:
            handler: Callable = route.handler
            sig = signature(handler)

            func_doc = parse_docstring(handler.__doc__ or "")
            responses: tuple[Response, ...] = unwrap_union_type(sig.return_annotation)

            if not all(get_origin(res) is Response for res in responses):
                continue

            pattern = route.pattern.decode("utf-8")
            path = paths[pattern][method.decode("utf-8").lower()] = {
                "description": func_doc["summary"],
                "parameters": [],
            }

            # Add parameter data (the data sent in the url)
            for _, param_name, _, _ in fmt.parse(pattern):
                if param_name is None:
                    continue

                # Since it has to be a simple type (like str or int),
                # no additional handling is required
                params.append(sig.parameters[param_name].annotation)

                parameter_schemas.append({})
                path["parameters"].append(
                    {
                        "name": param_name,
                        "in": "path",
                        "required": True,
                        "schema": parameter_schemas[-1],
                        "description": func_doc["parameters"].get(param_name, ""),
                    },
                )

            path["operationId"] = handler.__name__

            path["responses"] = {}
            for response in responses:
                status, klass = get_args(response)
                status = str(get_args(status)[0])

                body_and_response_schemas.append({})
                path["responses"][status] = {
                    "description": func_doc["responses"].get(status, ""),
                    "content": {
                        "application/json": {
                            "schema": body_and_response_schemas[-1],
                        },
                    },
                }

                types.append(klass)

            for klass in sig.parameters.values():
                annotation = klass.annotation
                origin = get_origin(annotation)

                if origin is not FromJSON:
                    continue

                body = get_args(annotation)[0]
                types.append(body)

                body_and_response_schemas.append({})
                path["requestBody"] = {
                    "description": func_doc["body"],
                    "content": {
                        "application/json": {
                            "schema": body_and_response_schemas[-1],
                        },
                    },
                }

    schemas, parameter_components = schema_components(
        params,
        ref_template="#/components/parameters/{name}",
    )
    for i, schema in enumerate(schemas):
        parameter_schemas[i].update(schema)

    schemas, components = schema_components(
        types,
        ref_template="#/components/schemas/{name}",
    )
    for i, schema in enumerate(schemas):
        body_and_response_schemas[i].update(schema)

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

    (Path.cwd() / "static" / "openapi.yaml").write_bytes(encode(clean(openapi)))


def bind_app(app: Application) -> None:
    app.on_start += build_docs
