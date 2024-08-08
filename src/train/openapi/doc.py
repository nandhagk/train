from collections import defaultdict
from inspect import signature
from typing import TYPE_CHECKING, Union, get_args, get_origin

from blacksheep import Application
from msgspec.json import schema_components

from train.utils import ENCODER

if TYPE_CHECKING:
    from collections.abc import Callable


def build_docs(app: Application) -> bytes:  # noqa: C901
    from train.app import FromJSON, Response

    types = []
    params = []
    idk_what_im_doing: list[dict] = []
    idk_what_im_doing_again: list[dict] = []

    paths = defaultdict(dict)
    for method, routes in app.router.routes.items():
        for route in routes:
            handler: Callable = route.handler
            sig = signature(handler)

            responses: tuple[Response, ...]
            if get_origin(sig.return_annotation) is Union:
                responses = get_args(sig.return_annotation)
            else:
                responses = (sig.return_annotation,)

            if not all(get_origin(res) is Response for res in responses):
                continue

            pattern = route.pattern.decode("utf-8")
            path = paths[pattern][method.decode("utf-8").lower()] = {}

            if "{" in pattern:
                param = pattern[pattern.find("{") + 1 : pattern.find("}")]
                params.append(sig.parameters[param].annotation)
                idk_what_im_doing_again.append({})
                path["parameters"] = [
                    {
                        "name": param,
                        "in": "path",
                        "required": True,
                        "schema": idk_what_im_doing_again[-1],
                        "description": "",
                    },
                ]

            path["operationId"] = handler.__name__

            path["responses"] = {}
            for response in responses:
                status, klass = get_args(response)
                status = str(get_args(status)[0])

                idk_what_im_doing.append({})
                path["responses"][status] = {
                    "description": "",
                    "content": {
                        "application/json": {
                            "schema": idk_what_im_doing[-1],
                        },
                    },
                }

                types.append(klass)

            for klass in sig.parameters.values():
                annotation = klass.annotation
                if get_origin(annotation) is not FromJSON:
                    continue

                args = get_args(annotation)
                assert len(args) == 1

                body = args[0]
                types.append(body)

                idk_what_im_doing.append({})
                path["requestBody"] = {
                    "description": "",
                    "content": {
                        "application/json": {
                            "schema": idk_what_im_doing[-1],
                        },
                    },
                }

    stuff, param_schema = schema_components(
        params,
        ref_template="#/components/parameters/{name}",
    )
    for i, p in enumerate(stuff):
        idk_what_im_doing_again[i].update(p)

    stuff, schema = schema_components(types, ref_template="#/components/schemas/{name}")
    for i, s in enumerate(stuff):
        idk_what_im_doing[i].update(s)

    openapi = {
        "openapi": "3.1.0",
        "info": {
            "title": "FTCB API",
            "version": "0.0.0-alpha",
        },
        "paths": paths,
        "servers": [],
        "components": {"schemas": schema, "parameters": param_schema},
    }

    return ENCODER.encode(openapi)
