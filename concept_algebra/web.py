"""Loopback HTTP worker for the Go site's /api/algebra proxy."""
import argparse
from collections import OrderedDict
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import logging
from pathlib import Path
import socket

from . import AlgebraError, ConceptAlgebra, ConceptGraph, parse
from .syntax import FACT_FUNCTIONS


MAX_BODY = 96 * 1024
MAX_HTTP_NODES = 256
MAX_HTTP_FACTS = 12


def error_document(exc):
    error = {"type": type(exc).__name__, "message": str(exc)}
    for field in ("position", "end", "line", "column", "candidates", "field"):
        if hasattr(exc, field):
            error[field] = getattr(exc, field)
    return {"error": error}


def checked_request(data):
    allowed = {"expression", "context", "within", "lang", "limit", "offset", "explain"}
    if not isinstance(data, dict) or set(data) - allowed:
        raise AlgebraError("Expected an expression object with supported request fields")
    expression = data.get("expression")
    if not isinstance(expression, str):
        raise AlgebraError("expression must be a string")
    within = data.get("within")
    if within is not None and not isinstance(within, str):
        raise AlgebraError("within must be a string or null")
    language = data.get("lang")
    if language not in (None, "en", "ru"):
        raise AlgebraError("lang must be en, ru, or null")
    for name, default, low, high in (("context", 1, 1, 5), ("limit", 25, 1, 100),
                                    ("offset", 0, 0, 1000000)):
        value = data.get(name, default)
        if type(value) is not int or not low <= value <= high:
            raise AlgebraError(f"{name} must be an integer from {low} to {high}")
    explain = data.get("explain")
    if explain is not None and (type(explain) is not int or not 1 <= explain <= 2147483647):
        raise AlgebraError("explain must be a positive concept ID or null")
    roots = []
    for field, source in (("expression", expression), ("within", within)):
        if field == "within" and (source is None or not source.strip()):
            continue
        try:
            roots.append(parse(source))
        except AlgebraError as exc:
            exc.field = field
            raise
    nodes = facts = 0
    pending = list(roots)
    while pending:
        node = pending.pop()
        nodes += 1
        facts += int(node.kind == "call" and node.value in FACT_FUNCTIONS)
        pending.extend(node.args)
    if nodes > MAX_HTTP_NODES or facts > MAX_HTTP_FACTS:
        raise AlgebraError("The web API allows 256 AST nodes and 12 property selectors across expression and domain")
    return {
        "expression": expression, "within": within if within and within.strip() else None,
        "context": data.get("context", 1), "lang": language,
        "limit": data.get("limit", 25), "offset": data.get("offset", 0), "explain": explain,
    }


class AlgebraService:
    """Single-worker cache. Data-version changes invalidate all context views."""
    def __init__(self, snapshot=None, version_file=None, loader=None):
        self.snapshot = snapshot
        self.version_file = Path(version_file) if version_file else None
        self.loader = loader or (lambda context: ConceptGraph.from_json(snapshot, context=context)
                                 if snapshot else ConceptGraph.from_database(context=context))
        self.graphs = OrderedDict()
        self.signature = None

    def version(self):
        if not self.version_file:
            return {}
        try:
            data = json.loads(self.version_file.read_text(encoding="utf-8-sig"))
            if not isinstance(data, dict):
                raise ValueError("Expected version metadata object")
            return {key: data[key] for key in ("code_version", "interface_revision", "data_revision", "source_dump_sha256") if key in data}
        except (OSError, ValueError, TypeError) as exc:
            raise AlgebraError("Graph version metadata is temporarily unavailable") from exc

    def graph(self, context):
        version = self.version()
        signature = (version.get("data_revision"), version.get("source_dump_sha256"))
        if self.snapshot:
            try:
                stat = Path(self.snapshot).stat()
                signature += (stat.st_mtime_ns, stat.st_size)
            except OSError as exc:
                raise AlgebraError("The graph snapshot is temporarily unavailable") from exc
        if signature != self.signature:
            self.graphs.clear()
            self.signature = signature
        if context not in self.graphs:
            self.graphs[context] = self.loader(context)
        self.graphs.move_to_end(context)
        while len(self.graphs) > 2:
            self.graphs.popitem(last=False)
        return self.graphs[context], version

    def evaluate(self, data):
        request = checked_request(data)
        graph, version = self.graph(request["context"])
        algebra = ConceptAlgebra(graph, language=request["lang"])
        result = algebra.evaluate(request["expression"], within=request["within"], explain=request["explain"])
        output = result.to_dict(limit=request["limit"], offset=request["offset"], include_ast=True, include_ids=True)
        output["source"] = version
        output["language_version"] = "1"
        return output

    def health(self):
        graph, version = self.graph(1)
        return dict(ok=True, concepts=len(graph.ids), source=version, language_version="1")


def make_handler(service):
    class Handler(BaseHTTPRequestHandler):
        server_version = "ConceptuumAlgebra/1"

        def setup(self):
            super().setup()
            self.connection.settimeout(10)

        def send_json(self, status, data, allow=None):
            payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            if allow:
                self.send_header("Allow", allow)
            self.end_headers()
            try:
                self.wfile.write(payload)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def do_GET(self):
            if self.path != "/health":
                self.send_json(405, {"error": {"message": "Use POST /evaluate"}}, allow="POST")
                return
            try:
                self.send_json(200, service.health())
            except AlgebraError as exc:
                self.send_json(503, error_document(exc))
            except Exception:
                logging.exception("Algebra health check failed")
                self.send_json(503, {"error": {"message": "Concept algebra is temporarily unavailable"}})

        def do_POST(self):
            if self.path != "/evaluate":
                self.send_json(404, {"error": {"message": "Unknown API path"}})
                return
            if self.headers.get_content_type() != "application/json":
                self.send_json(415, {"error": {"message": "Use application/json"}})
                return
            try:
                raw_length = self.headers.get("Content-Length", "")
                if len(raw_length) > 10 or not raw_length.isascii() or not raw_length.isdecimal():
                    raise AlgebraError("A valid Content-Length is required")
                length = int(raw_length)
                if not 0 < length <= MAX_BODY:
                    self.send_json(413, {"error": {"message": "Request exceeds the body limit"}})
                    return
                payload = self.rfile.read(length)
                if len(payload) != length:
                    raise AlgebraError("Incomplete request body")
                try:
                    data = json.loads(payload.decode("utf-8"))
                except (ValueError, UnicodeError, RecursionError):
                    raise AlgebraError("Request body must be a valid UTF-8 JSON object") from None
                self.send_json(200, service.evaluate(data))
            except AlgebraError as exc:
                self.send_json(422, error_document(exc))
            except (socket.timeout, TimeoutError):
                self.send_json(408, {"error": {"message": "Request timed out"}})
            except Exception:
                logging.exception("Algebra request failed")
                self.send_json(503, {"error": {"message": "Concept algebra is temporarily unavailable"}})

        def log_message(self, format, *args):
            # Requests use a fixed path; expressions and credentials are not logged.
            logging.info(format, *args)

    return Handler


def main():
    parser = argparse.ArgumentParser(description="Run the loopback concept algebra worker for the Go visualizer")
    parser.add_argument("--host", choices=["127.0.0.1", "localhost"], default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7101)
    parser.add_argument("--snapshot", help="optional JSON snapshot instead of MariaDB")
    parser.add_argument("--version-file", help="version.json; a data revision change invalidates cached graphs")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("port must be from 1 to 65535")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    service = AlgebraService(args.snapshot, args.version_file)
    server = HTTPServer((args.host, args.port), make_handler(service))
    logging.info("Concept algebra listening on %s:%d", args.host, args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
