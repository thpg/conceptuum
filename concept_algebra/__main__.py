"""Usage: python -m concept_algebra '#25439 & #25446' --context 1 --json"""
import argparse
import json
import sys

from . import AlgebraError, ConceptAlgebra, parse


def nonnegative(text):
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError("expected a nonnegative integer") from None
    if value < 0:
        raise argparse.ArgumentTypeError("expected a nonnegative integer")
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description="Evaluate concept algebra against a read-only graph snapshot.")
    parser.add_argument("expression", help="expression, or - to read up to 8192 characters from stdin")
    parser.add_argument("--context", type=int, default=1, help="relation universum ID (default: 1)")
    parser.add_argument("--within", help="set expression defining U and the output domain")
    parser.add_argument("--lang", help="term lookup and display language, e.g. en or ru; default: all languages")
    parser.add_argument("--snapshot", help="JSON table snapshot instead of the configured MariaDB database")
    parser.add_argument("--limit", type=nonnegative, default=20, help="display at most this many members; 0 displays all")
    parser.add_argument("--json", action="store_true", help="emit a structured result, including the resolved ID expression")
    parser.add_argument("--ast", action="store_true", help="parse only and print the AST; no database connection")
    parser.add_argument("--explain", type=int, metavar="ID", help="inspect a record in the result or the operands of a comparison/count")
    args = parser.parse_args(argv)
    expression = sys.stdin.read(8193) if args.expression == "-" else args.expression
    try:
        # Catch malformed expressions before opening a database connection.
        ast = parse(expression)
        if args.ast:
            print(json.dumps(ast.to_dict(), ensure_ascii=False, indent=2))
            return 0
        if args.within is not None:
            parse(args.within)
        if args.snapshot:
            algebra = ConceptAlgebra.from_json(args.snapshot, context=args.context, language=args.lang)
        else:
            algebra = ConceptAlgebra.from_database(context=args.context, language=args.lang)
        result = algebra.evaluate(expression, within=args.within, explain=args.explain)
        data = result.to_dict(limit=args.limit or None)
        if args.json:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print(f"Catalog algebra | U{data['context']} | domain: {data['universe_count']} records")
            print(data["resolved_expression"])
            if result.kind == "set":
                print(f"{data['count']} concept record(s)")
                for item in data["items"]:
                    print(f"  #{item['id']}  {item['name']}")
                if data["truncated"]:
                    print(f"Showing {data['returned']} of {data['count']}; use --limit 0 for all.")
            else:
                print(json.dumps(data["value"]))
            if args.explain is not None:
                print(json.dumps(data["explanation"], ensure_ascii=False, indent=2))
        return 0
    except AlgebraError as exc:
        error = {"type": type(exc).__name__, "message": str(exc)}
        for field in ("position", "end", "line", "column", "candidates", "field"):
            if hasattr(exc, field):
                error[field] = getattr(exc, field)
        if args.json:
            print(json.dumps({"error": error}, ensure_ascii=False), file=sys.stderr)
        else:
            print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
