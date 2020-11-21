"""A GenerateCommand Command."""
import json
import os
import inspect
import yaml
from config.database import Model
from typing import List, Dict, Tuple
from pathlib import Path
from cleo import Command
from routes.web import ROUTES

project_directory = Path(__file__).parent.parent.parent


class GenerateCommand(Command):
    """
    Generates valid OpenAPI 3.0 from application

    openapi:generate
        {name : optional alternative filename, default=OpenAPI.yaml}
    """

    @staticmethod
    def _checks(endpoint: object) -> bool:
        """
        Runs a set of pre-flight checks to avoid common/expected errors
        Returns a boolean indicating success/failure
        """

        # Controller instanciation check
        if not hasattr(endpoint, "controller"):
            endpoint._find_controller(endpoint.output)

        # Index sanity check
        elif endpoint.route_url == "/":
            return False

        # Model check
        elif not hasattr(endpoint.controller, "model"):
            return False

        else:  # Default
            return True

    @staticmethod
    def _create_components(endpoint: object, model: Model) -> List[Tuple]:
        """
        Attempts to reverse engineer masonite's endpoints
        to retrieve method annotations for schema generation

        Arguement(s):
        - endpoint <object>: the endpoint to reverse engineer
        - model <object>: model to create schema for
        """
        openapi_types = [str, int, float, list, dict, tuple]
        components: dict = {"schemas": {}}

        # Retrieve list of endpoint controller methods
        # (name, method)
        controller_methods: List[Tuple[str, object]] = inspect.getmembers(
            object=endpoint.controller, predicate=inspect.isfunction
        )

        # Fish out the controller __init__ from the list
        [
            controller_methods.remove(method)
            for method in controller_methods
            if method[0] == "__init__"
        ]

        # Retrieve the method and read annotations
        for method in controller_methods:

            # Wrong method, try another one.
            if method[0] != endpoint.controller_method:
                continue

            # Retrieve our annotations
            annotations = method[1].__annotations__

            # Can't process what's not there.
            if "return" not in annotations.keys():
                continue

            # Retrieve input values
            input_values: dict = annotations.copy()
            input_values.pop("return")

            # Populate properties with the input data
            properties: dict = {}
            for input_name, input_type in input_values.items():
                if type(input_type) not in openapi_types:
                    # Then we set it as generic
                    input_type = "object"

                properties[input_name] = {"type": input_type}

            # Create component schema for the model
            components["schemas"][model] = {
                "title": model,
                "type": "object",
                "properties": properties,
            }

        return components

    @staticmethod
    def _recompile_route(endpoint: object) -> str:
        """Attempts to re-compile the masonite route
        to valid OpenAPI valid schema"""

        segments: list = endpoint.route_url.split("/")
        last_segment = segments[len(segments) - 1]

        route: str = ""
        for segment in segments:
            if segment.startswith("@"):
                segment = segment.replace("@", ":")
            elif segment == "" and route != "/":
                segment = "/"
            elif segment != "" and route == "/" and segment != last_segment:
                segment += "/"
            else:
                pass

            route += segment

        return route

    @staticmethod
    def _get_model(endpoint: object) -> Model:
        """Attempts to retrieve the model using the current endpoint"""

        # Model presence check
        if hasattr(endpoint.controller, "model"):
            return endpoint.controller.model
        else:
            return (
                str(endpoint.controller.__name__)
                .replace("Controller", "")
                .capitalize()
            )

    @staticmethod
    def _create_status_codes(endpoint: object) -> dict:
        """Attempts to create status codes for provided endpoint"""

        # TODO: Auth & Redirects

        # Success cases
        if endpoint.method_type == ["GET"]:
            success_case = "200", "OK"
        elif endpoint.method_type == ["POST"]:
            success_case = "201", "Created"
        else:
            success_case = "204", "No-content"

        # Error cases
        if hasattr(endpoint, "url_list"):
            error_case = "500", "Internal Server Error"

        # Failure cases
        if hasattr(endpoint, "url_list"):
            failure_case = "400", "Bad Request"

        status_types: dict = {
            "success": success_case,
            "error": error_case,
            "failure": failure_case,
        }

        return status_types

    @staticmethod
    def _create_responses(
        endpoint: object, model: object, status_codes: dict
    ) -> dict:
        """
        Attempts to create response schema

        Argument(s):
        - endpoint <object>: the current endpoint being processed
        - status_codes <dict>: generated list of status_codes

        Returns
        - response_schema <dict>: generated responses
        """

        # TODO: Create error models | use built-ins for dynamic responses
        # TODO: Handle one/many

        responses = {
            status_codes["success"][0]: {
                "description": status_codes["success"][1],
                "content": {
                    "application/json": {
                        "schema": {"$ref": f"#/components/schemas/{model}"}
                    }
                },
            },
            status_codes["error"][0]: {
                "description": status_codes["error"][1],
                "content": {
                    "application/json": {"schema": {"type": "string"}}
                },
            },
            status_codes["failure"][0]: {
                "description": status_codes["failure"][1],
                "content": {
                    "application/json": {"schema": {"type": "string"}}
                },
            },
        }

        return responses

    @staticmethod
    def _create_tags(
        endpoint: object, global_tags: list, used_tags: list
    ) -> List[Dict]:
        """
        Looks up all available tags for the endpoint.
        If no tags are found controller name will be used as default.

        Argument(s):
        - endpoint <object>: the current endpoint being processed
        - global_tags <list>: list of global specification tags
        - used_tags <list>: temporary store for the tags during processing

        Returns compiled tags
        """

        # Case many
        if hasattr(endpoint.controller, "tags"):  # Get the tags
            tags = endpoint.controller.tags
            if tags not in used_tags:
                for tag in tags:
                    global_tags.append(
                        {
                            "name": tag,
                            "description": f"Grouping for {tag} endpoints",
                        }
                    )
                    used_tags.append(tags)

        # Case one
        else:  # Create a tag
            tags = [(
                (endpoint.controller.__name__)
                .replace("Controller", "")
                .capitalize()
            )]
            if tags not in used_tags:
                global_tags.append(
                    {
                        "name": tags,
                        "description": f"Grouping for {tags} endpoints",
                    }
                )
                used_tags.append(tags)

        # Return
        return tags

    @staticmethod
    def _update_paths(paths, endpoint, route, tags, responses):
        endpoint_type = endpoint.method_type[0].lower()
        endpoint_name = str(endpoint.output).replace("@", ".")

        paths[route] = {
            endpoint_type: {
                "operationId": f"{endpoint.module_location}.{endpoint_name}",
                "description": endpoint.controller.__doc__,
                "summary": f"Endpoint '{route}' handled by '{endpoint_name}'",
                "tags": tags,
                "responses": responses,
            }
        }

        if not endpoint.url_list:
            return

        for argument_name in endpoint.url_list:
            paths[route][endpoint_type]["parameters"] = [
                {
                    "schema": {"type": "string"},
                    "in": "query",  # TODO multiple-args-types
                    "name": str(argument_name),
                }
            ]

    @staticmethod
    def _write_specification(
        specification: dict,
        filename: str = "openapi",
        format: str = "json",
        output: bool = "file",
    ):
        """
        Writes specification to output or file.

        Argument(s):
        - specification <dict>:   specification to write (Required)
        - filename <str>: filename to set for the specification,
            default='openapi.extension`
        - format <str>:   format option to use,
            available options: `json` | `yaml`, default='json'
        - output <str>:   output option to use,
            available options: `file` | 'print', 'default='file'
        """

        if format == "json" and output == "file":
            with open(f"{filename}.json", "w") as file:
                json.dump(specification, file, indent=4)
        elif format == "yaml" and output == "file":
            with open(f"{filename}.yaml", "w") as file:
                yaml.dump(specification, file, indent=4)
        else:
            print(json.dumps(obj=specification, indent=4))

    def handle(self):
        global_tags = []
        used_tags = []
        paths = {}

        base: dict = {
            "openapi": "3.0.0",
            "info": {
                "title": os.getenv("APP_NAME") or "Masonite OpenAPI App",
                "version": os.getenv("APP_VERSION") or "testing",
                "contact": {
                    "name": os.getenv("CONTACT_EMAIL") or "John Doe",
                    "url": f"{os.getenv('APP_URL')}/contact"
                    or "http://localhost:8000/contact",
                    "email": os.getenv("CONTACT_EMAIL") or "john@example.com",
                },
                "termsOfService": os.getenv("APP_TERMS_OF_SERVICE")
                or "/contact",
                "description": os.getenv("APP_DESCRIPTION")
                or "Masonite OpenAPI Specification",
            },
            "servers": [
                {"url": os.getenv("APP_URL") or "http://localhost:8000"}
            ],
        }

        # Go through available endpoints
        for endpoint in ROUTES:
            # Run endpoint checks
            if self._checks(endpoint):
                continue

            # Generetate components
            route: str = self._recompile_route(endpoint)
            model = self._get_model(endpoint)
            statuses = self._create_status_codes(endpoint)
            responses = self._create_responses(endpoint, model, statuses)
            local_tags = self._create_tags(endpoint, global_tags, used_tags)

            # Update paths
            self._update_paths(paths, endpoint, route, local_tags, responses)

        # Add remaining global data
        base["tags"] = global_tags
        base["paths"] = paths
        base["components"] = self._create_components(endpoint, model)

        # Make the spec!
        self._write_specification(base)
