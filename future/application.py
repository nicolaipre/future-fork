from future.logger import setup_logging
from future.request import Request
from future.response import Response
from future.routing import Route, RouteGroup, RouteMatch
from future.middleware import Middleware
from future.types import ASGIScope, ASGIReceive, ASGISend
from typing import TypedDict, Callable, Optional, Union, Any, Sequence
from rich.console import Console
from rich import print
from re import Pattern
import logging
import uvicorn
import traceback
import asyncio
import httpx
import enum
from pwn import log
import re

"""
+        except BaseException:
+            event_type = "lifespan.shutdown.failed" if started else "lifespan.startup.failed"
+            await send({"type": event_type, "message": traceback.format_exc()})
+            raise
+        await send({"type": "lifespan.shutdown.complete"})
         
-        # Custom openapi path
-        if path == "/openapi.json":
-            await self.serve_openapi(send)
-            return
+        while True:
+            message = await receive()
+            print(f"Got message:", message)
"""

"""
# This module configures the BlackSheep application before it starts.
from blacksheep import Application
from rodi import Container
from app.auth import configure_authentication
from app.docs import configure_docs
from app.errors import configure_error_handlers
from app.services import configure_services
from app.settings import load_settings, Settings

def configure_application(services: Container, settings: Settings) -> Application:
    app = Application(services=services, show_error_details=settings.app.show_error_details)
    configure_error_handlers(app)
    configure_authentication(app, settings)
    configure_docs(app, settings)
    return app

app = configure_application(*configure_services(load_settings()))
"""

setup_logging()


class RegexConfig(TypedDict):
    paths: list[Pattern]

class EndpointConfig(TypedDict):
    endpoint: Callable
    middleware_before: list[Middleware]
    middleware_after: list[Middleware]
    regex: Optional[RegexConfig]



""" # ASGI SPEC
async def application(scope, receive, send):
    event = await receive()
    ...
    await send({"type": "websocket.send", ...: ...})


example_http_event = {
    "type": "http.request",
    "body": b"Hello World",
    "more_body": False,
}

example_websocket_event = {
    "type": "websocket.send",
    "text": "Hello world!",
}

example_http_scope = {
    'type': 'http',
    'method': 'POST',
    'path': '/echo',
    'headers': [...],
    ...: ...,
}
"""

class AsgiEventType(enum.StrEnum):
    LIFESPAN_STARTUP = "lifespan.startup"
    LIFESPAN_STARTUP_COMPLETE = "lifespan.startup.complete"
    LIFESPAN_STARTUP_FAILED = "lifespan.startup.failed"

    LIFESPAN_SHUTDOWN = "lifespan.shutdown"
    LIFESPAN_SHUTDOWN_COMPLETE = "lifespan.shutdown.complete"
    LIFESPAN_SHUTDOWN_FAILED = "lifespan.shutdown.failed"

    ...



#@dataclass
class Lifespan:
    #app: ASGIApp
    def __init__(self, app):
        self.app = app

    async def __aenter__(self):
        async with asyncio.timeout(10):
            log.info(message="\t  Running startup rotuine...")
            await startup_wait(self.app)
        return { "machine_id": 42 }

    async def __aexit__(self, exc_type, exc_value, tb) -> bool | None:
        async with asyncio.timeout(10):
            log.info(message="\t  Running shutdown routine...")
            await shutdown_wait(self.app)
        return None


async def startup_wait(app):
    ...
    #await asyncio.sleep(5)

async def shutdown_wait(app):
    ...
    #await asyncio.sleep(5)


"""
async def lifespan(app):
    log.info("Starting up...")
    app.db = await init_db()
    app.s3_client = await init_boto_s3()
    app.redis_client = await init_redis()
    app.settings.dynamic = await read_dynamic_settings(app.db)
    app.sanity_check_settings()
    app.spawn_metrics_worker()
    yield
    log.info("Shutting down...")
    await app.save_metrics(app.db)
    await email_devops()  # :)

    async with asyncio.timeout(30):
        print("startup things")
        await startup_wait(app)
        #await could_hang_forever()
    try:
        #yield # { "a": "b" } # yields stuff into scope
        yield { "machine_id": 42 }  # state copied to every request
    finally:
        async with asyncio.timeout(30):
            await shutdown_wait(app)
            print("shutdown things")
"""



class Future:
    def __init__(self, lifespan, name: str = "Future", debug: bool = False, domain: str = ""):
        # spawn background tasks in the lifespan startup process... or database connections etc...
        # on shutdown, save shit, send info about shutdown etc...
        self.lifespan = lifespan
        self.debug = debug  # Implement: https://asgi.readthedocs.io/en/stable/extensions.html#debug
        self.domain = domain
        self.logger = logging.getLogger(name)
        self.routes: dict[str, list[EndpointConfig]] = {}
        #self.routes: dict[str, dict[str, EndpointConfig]] = {}

        # self.middleware_manager = MiddlewareManager(self.dispatch)
        # Add openAPI after all rotues are added with add_routes()
        # self._add_to_openapi(path, subdomain, methods, summary)

    """
    def _add_to_openapi(self, path: str, subdomain: str, methods: list[str], summary: str, description: str = "Successful Response"):
        if subdomain:
            full_path = f"/{subdomain}.{path.lstrip('/')}"
        else:
            full_path = path
        if full_path not in self.openapi_schema["paths"]:
            self.openapi_schema["paths"][full_path] = {}
        for method in methods:
            self.openapi_schema["paths"][full_path][method.lower()] = {
                "summary": summary,
                "responses": {"200": {"description": description}},
            }
    """

    #def _add_route(self, path: str, endpoint: Callable, subdomain: str = None, methods: list[str] = ["GET"], name: str = "", middlewares: list[Middleware] = [], regex=None) -> None:
    def _add_route(self, route: Route, subdomain: str = "") -> None:
        """Internal method to add single routes to the application.

        Args:
            route (Route): The actual route object
            subdomain (str): The subdomain the route should (only) be available for. Defaults to "" (all).
        """

        # FIXME: This is no point in having??? Or is it just to prevent key error?? Rather just fix the key error?? or, maybe it is because of .append() later on?
        if subdomain not in self.routes:
            self.routes[subdomain] = []

        # TODO: do we want to be kind here and add a fail-safe that notifies the user and exits if the user attempts to overwrite an existing entry?

        # old: if path not in self.routes[subdomain]:
            #self.routes[subdomain][path] = {}

        # Iterate over middlewares and put these in their respective before/after dicts
        before = []
        after = []
        # old: for middleware in middlewares:
        for middleware in route.middlewares:
            if middleware.attach_to == "request":
                before.append(middleware)
            elif middleware.attach_to == "response":
                after.append(middleware)

        # Sort based on middleware priority # TODO: Check that the order is correct
        before.sort(key=lambda middleware: middleware.priority)
        after.sort(key=lambda middleware: middleware.priority)

        endpoint_config = EndpointConfig(
            #endpoint=route.endpoint,
            middleware_before=before,
            middleware_after=after,
            #regex={"paths": [route._rx]},
            #og_path=route.path,
            #_rx={"paths": [regex]},
            route=route  # Include the full Route object
        )

        # Sort based on middleware priority # Is this done? Check the order lol
        before.sort(key=lambda middleware: middleware.priority)
        after.sort(key=lambda middleware: middleware.priority)

        # old: self.routes[subdomain][path]["endpoint"] = endpoint
        # old: self.routes[subdomain][path]["middleware_before"] = before
        # old: self.routes[subdomain][path]["middleware_after"] = after
        self.routes[subdomain].append(endpoint_config)

        # TODO: Forbedre dicten over til nock sitt forslag:
        """
        {
            "<endpoint>": {
                "handler": "<route handler callable>",
                "middleware": {
                    "before_handlers": ["< sorted handlers callable>"]
                    "after_handlers": ["< sorted handlers callable>"]
                },
                "regex?": {
                    "paths": ["<compiled regex>", ...]
                }
            }
        }
        """

    # old: def add_routes(self, routes: list[Route, RouteGroup]) -> None:
    def add_routes(self, routes: Sequence[Union[Route, RouteGroup]]) -> None:
        for r in routes:
            if isinstance(r, Route):  # Single route
                self._add_route(
                    route=r,
                    subdomain="",
                )
            elif isinstance(r, RouteGroup):  # Grouped routes
                for route in r.routes:
                    route.path = f"{r.prefix}{route.path}"  # Convert route.path to full path (group.prefix AND route.path)
                    route.middlewares = r.middlewares + route.middlewares  # Combine route-specific middlewares with group middlewares
                    
                    # Now lets compile the regex for the new path before we add it
                    route.compile_pattern()
                    
                    # Finally, we add the route group
                    self._add_route(
                        route=route,
                        subdomain=r.subdomain,
                    )
            else:
                raise NotImplementedError


    async def handle_lifespan_request(self, scope: ASGIScope, receive: ASGIReceive, send: ASGISend) -> None:
        # initialize_scheduler for cronjobs
        
        assert scope["type"] == "lifespan"
        message = await receive()
        assert message["type"] == "lifespan.startup"
        started = False
        app = scope.get("app")
        
        try:
            async with self.lifespan(app) as state:
                if state is not None:
                    scope["state"].update(state)
                await send({"type": "lifespan.startup.complete"})
                started = True
                message = await receive()
                assert message["type"] == "lifespan.shutdown"
                
        except BaseException:
            event_type = "lifespan.shutdown.failed" if started else "lifespan.startup.failed"
            await send({"type": event_type, "message": traceback.format_exc()})
            raise
        
        await send({"type": "lifespan.shutdown.complete"})
        
        """
        while True:
            message = await receive()
            print(f"Got message:", message)

            if message["type"] == "lifespan.startup":
                # scope["state"]["GlobalKey"] = "Value"
                await send({"type": "lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                await send({"type": "lifespan.shutdown.complete"})
                break
        """


    async def handle_http_request(self, scope: ASGIScope, receive: ASGIReceive, send: ASGISend) -> None:
        request = Request(scope, receive)

        # Grab the host header
        host_header_parts = request.host.split(".") if request.host else []

        # Strip the port away, we don't care about it
        if ":" in request.host:
            host_header = request.host.split(":")[0]
        else:
            host_header = request.host

        # Check if host is an IP address
        if host_header.replace(".", "").isdigit():  # Simple check for IPv4  # TODO: do we need this? Is it even worth checking?
            domain = None
            subdomain = None
        else:
            # TODO - nock: Direct match self.domain med subdomain på host-feltet
            # With debug=True, just parse subdomains as usual since we set the Host header to test:
            # 🚀 Recommended: Use option 1 (Host header rewrite) so debug mode behaves like production:         # curl -H "Host: sub.example.com" http://127.0.0.1:8000/your-route
            # Get all parts except the last two (which form the domain)
            # subdomain = host_header_parts[0] if len(host_header_parts) > 2 else ""
            # FIXME: Yes, I know. This is shitty. We will fix this later to allow nested subdomains/RouteGroups, probably.
            # Original line (has issues with IP addresses and ports):
            # subdomain = ".".join(host_header_parts[:-2]) if len(host_header_parts) > 2 else ""
            #domain = (host_header_parts[-2] + "." + host_header_parts[-1] if len(host_header_parts) > 1 else "")  # old
            #domain = re.search(r'([^.]+\.[^.]+)$', host).group(1) if re.search(r'([^.]+\.[^.]+)$', host) else ""  # Solution 1: Get just the top level domain (example.com)
            domain = re.search(r'(?:[^.]+\.)?(.+)$', host_header).group(1) if re.search(r'(?:[^.]+\.)?(.+)$', host_header) else ""  #  Solution 2: Get everything except first subdomain (api.example.com from dev.api.example.com)
            #subdomain = ".".join(host_header_parts[:-2]) if len(host_header_parts) > 2 else ""
            subdomain = host_header_parts[0] if len(host_header_parts) > 2 else ""


        # FIXME: should we care about the domain being set or not in debug mode? No... Probably not. Yes, we should. Debug mode = ALlowed, Prod = not allowed unless host header matches domain.
        # Host header not matching domain AND not in debug mode, yeeet it
        if domain != self.domain and not self.debug:
            response = Response(body=b"Not Found", status=404)
            await response(send)
            return

        """
        # Custom OpenAPI path  TODO: Move dis bitch somewhere else...
        if path == "/openapi.json":
            await self.serve_openapi(send)
            return
        """

        route_params = None
        matched_route = None
        request_path = request.path.encode()
        subdomain_routes = self.routes.get(subdomain, [])  # EndpointConfig list

        for epc in subdomain_routes:
            route: Route = epc["route"]
            route_match: RouteMatch = route.match(request_path)
            if route_match:
                matched_route = epc
                route_params = route_match.params
                break

        if not matched_route:
            response = Response(body=b"Not Found", status=404)
            await response(send)
            return


        log.debug(f"Congratulations. You hit a valid route and didn't fuck anything up (at least until now..)")  # type: ignore[reportUnknownMemberType]
        # Process middlewares in reverse order?
        # for middleware in reversed(self.middlewares): ...
        # old: Ok, the endpoint exists and has a match. Check if it has any before or after middlewares
        # old: middleware_before = subdomain_routes.get(path).get("middleware_before", None)
        # old: middleware_after = subdomain_routes.get(path).get("middleware_after", None)
        # FIXME: error handling for this, if endpoint is None
        #endpoint = subdomain_routes.get(request_path).get('endpoint', None)
        endpoint = matched_route["route"].endpoint
        middleware_before = matched_route["middleware_before"]
        middleware_after = matched_route["middleware_after"]

        # 1. Pre-processing (middleware before)
        for b_middleware in middleware_before:
            response = b_middleware.intercept(request)
            if response is not None:
                await response(send)
                return

        # 2. Endpoint functionality
        if route_params:
            response = await endpoint(request, **route_params)
        else:
            response = await endpoint(request)

        # 3. Post-processing (middlewares after)
        for a_middleware in middleware_after:
            modified_response = a_middleware.intercept(request, response)
            if modified_response is not None:
                response = modified_response

        await response(send)




        
    async def handle_websocket_request(self, scope: ASGIScope, receive: ASGIReceive, send: ASGISend) -> None:
        raise NotImplementedError

    async def __call__(self, scope: ASGIScope, receive: ASGIReceive, send: ASGISend) -> None:
        # path = scope["path"]

        # Inject ourselves into the chain for later convenience
        scope["app"] = self

        # Check scope type and handle accordingly...
        if scope["type"] == "lifespan":
            #log.debug("Handling lifespan stuff...")
            await self.handle_lifespan_request(scope, receive, send)
        elif scope["type"] == "http":
            await self.handle_http_request(scope, receive, send)
        elif scope["type"] == "websocket":
            await self.handle_websocket_request(scope, receive, send)
        else:
            raise NotImplementedError


    # FIXME: should this also be async?
    def run(self, host: str = "127.0.0.1", port: int = 8000, workers: int = 4, tls_key: Optional[str] = None, tls_cert: Optional[str] = None, tls_password: Optional[str] = None) -> None:
        # Slight rip from Blacksheep (sorry, it was too cool not to...)
        console = Console()
        console.rule("[bold yellow]Running for local development", align="left")
        console.print(f"[bold yellow]Visit http://localhost:{port}/docs")
        uvicorn.run(
            app="__main__:app", # "app.main.app"
            host=host,
            port=port,
            workers=workers,
            reload=self.debug,
            ssl_keyfile=tls_key,
            ssl_certfile=tls_cert,
            ssl_keyfile_password=tls_password,
            timeout_graceful_shutdown=3,
            log_level="info",
            lifespan="on",
        )

        #os.environ["APP_ENV"] = "dev"
        #port = int(os.environ.get("APP_PORT", 44777))
        # FIXME: move debug flag to app.run() instead of Future()

        # https://github.com/sanic-org/sanic/blob/a575f5c8858248680653c5a5b9565be4dcc56f9a/sanic/application/logo.py#L12    
        # https://github.com/sanic-org/sanic/blob/a575f5c8858248680653c5a5b9565be4dcc56f9a/guide/webapp/display/layouts/home.py#L29
        """
        ┌──────────────────────────────────────────────────────────────────────────────┐
        │                                Sanic v23.12.2                                │
        │                      Goin' Fast @ http://127.0.0.1:9000                      │
        ├───────────────────────┬──────────────────────────────────────────────────────┤
        │                       │      app: Future                                     │
        │     ▄███ █████ ██     │     mode: debug, single worker                       │
        │    ██                 │   server: sanic, HTTP/1.1                            │
        │     ▀███████ ███▄     │   python: 3.13.2                                     │
        │                 ██    │ platform: macOS-15.3.1-arm64-arm-64bit-Mach-O        │
        │    ████ ████████▀     │ packages: sanic-routing==23.12.0, sanic-ext==23.12.0 │
        │                       │                                                      │
        │ Build Fast. Run Fast. │                                                      │
        └───────────────────────┴──────────────────────────────────────────────────────┘
        """
