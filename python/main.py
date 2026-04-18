import argparse
import json
import sys
import python.generator as generator
import python.solver as solver

COMBINATION_LIMIT = 4_000_000


# ── Helpers ────────────────────────────────────────────────────────────────────
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, "item"):   # numpy scalar → plain Python type
            return obj.item()
        return super().default(obj)

def respond(obj):
    print(json.dumps(obj, cls=NumpyEncoder), flush=True)


# ── Counter ────────────────────────────────────────────────────────────────────
def total_count(*param_specs) -> int:
    total = 1
    for spec in param_specs:
        total *= generator.param_count(spec)
    return total

def update_param(param_list: list, updated_spec) -> int:
    param_list[:] = [updated_spec if s.name == updated_spec.name else s for s in param_list]
    return total_count(*param_list)


# ── Template Resolution ───────────────────────────────────────────────────────
def resolve_specs(req: dict):
    """Resolve params/influences from either a template name or explicit specs."""
    template_name = req.get("template")
    if template_name:
        tmpl = generator.get_template(template_name)
        return tmpl.params, tmpl.influences, tmpl.filter_fn, tmpl.name
    specs      = [generator.param(**p) for p in req.get("params", [])]
    influences = [generator.influence(**i) for i in req.get("influences", [])]
    return specs, influences, None, None


# ── Server ─────────────────────────────────────────────────────────────────────
def cmd_serve(_):
    """Persistent stdio loop."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError as e:
            respond({"error": f"invalid JSON: {e}"})
            continue

        command = req.get("command")
        limit   = req.get("limit", COMBINATION_LIMIT)

        if command == "list_templates":
            respond({"command": "list_templates", "templates": generator.list_templates()})
            continue

        specs, influences, filter_fn, template_name = resolve_specs(req)
        total = total_count(*specs)

        if command == "count":
            respond({"command": "count", "count": total, "limit": limit, "ok": total <= limit})

        elif command == "generate":
            if total > limit:
                respond({"command": "generate", "ok": False,
                         "warning": f"{total:,} exceeds limit of {limit:,}", "count": total})
                continue
            items = generator.cartesian_generator(
                *specs, influences=influences, filter_fn=filter_fn, template_name=template_name)
            for item in items:
                respond({"generation": item})
            respond({"done": True, "total": len(items)})

        elif command == "solve":
            if total > limit:
                respond({"command": "solve", "ok": False,
                         "warning": f"{total:,} exceeds limit of {limit:,}", "count": total})
                continue
            items = generator.cartesian_generator(
                *specs, influences=influences, filter_fn=filter_fn, template_name=template_name)

            # build constraints from request (or template defaults in future)
            constraints = [
                solver.ConstraintSpec(
                    name=c["name"], kind=solver.ConstraintKind(c["kind"]),
                    param_name=c["param_name"], bound=c["bound"],
                ) for c in req.get("constraints", [])
            ]
            request = solver.SolveRequest(
                items=items,
                constraints=constraints,
                objective_param=req.get("objective_param", "demand"),
                objective_sense=solver.Sense(req.get("objective_sense", solver.Sense.MAXIMIZE)),
            )
            result = solver.optimize(request)
            respond({
                "command": "solve",
                "objective_value": result.objective_value,
                "selections": result.selections,
                "total_generated": len(items),
                "total_selected": len(result.selections),
            })

        # TODO: "solve_multi" — multi-space optimisation
        # elif command == "solve_multi":
        #     spaces = req.get("spaces", [])
        #     global_constraints = req.get("global_constraints", [])
        #     ...

        else:
            respond({"error": f"unknown command: {command!r}"})


# ── CLI Parsers ────────────────────────────────────────────────────────────────
def parse_kwargs(parts: list[str]) -> dict:
    kwargs = {}
    for part in parts:
        k, _, v = part.partition("=")
        try:
            kwargs[k] = float(v) if "." in v else int(v)
        except ValueError:
            kwargs[k] = v
    return kwargs

def parse_param(raw: str) -> generator.ParamSpec:
    parts = raw.split(":")
    if len(parts) < 4:
        raise argparse.ArgumentTypeError(f"--param must be name:dist:min:max[:key=val ...], got: {raw}")
    name, dist, mn, mx = parts[:4]
    return generator.param(name, dist, float(mn), float(mx), **parse_kwargs(parts[4:]))

def parse_influence(raw: str) -> generator.InfluenceRule:
    parts = raw.split(":")
    if len(parts) < 3:
        raise argparse.ArgumentTypeError(f"--influence must be source:target:fn[:key=val ...], got: {raw}")
    source, target, fn = parts[:3]
    return generator.influence(source, target, fn, **parse_kwargs(parts[3:]))

def parse_constraint(raw: str) -> solver.ConstraintSpec:
    """name:kind:param_name:bound  e.g. budget:sum_le:price:10000"""
    parts = raw.split(":")
    if len(parts) < 4:
        raise argparse.ArgumentTypeError(f"--constraint must be name:kind:param:bound, got: {raw}")
    return solver.ConstraintSpec(
        name=parts[0], kind=solver.ConstraintKind(parts[1]),
        param_name=parts[2], bound=float(parts[3]),
    )


# ── CLI ────────────────────────────────────────────────────────────────────────
EPILOG = """
distributions:  uniform  gaussian  power  geometric  step
influence fns:  scale    offset    clamp
constraint kinds: sum_le  sum_ge  sum_eq

param kwargs:
  uniform/gaussian/power/geometric  resolution=N
  gaussian                          mean=F  std=F
  power                             bias=F
  step                              step=F

examples:
  python main.py serve
  python main.py templates
  python main.py generate --template generic_product
  python main.py generate --param price:power:10:1000:bias=1.5 --param demand:uniform:1:500
  python main.py solve    --template generic_product --constraint budget:sum_le:price:10000
  python main.py count    --param price:power:10:1000 --param demand:uniform:1:500:resolution=500
"""

def add_param_args(p):
    p.add_argument("--template",   metavar="NAME", help="use a registered template instead of manual params")
    p.add_argument("--param",      metavar="name:dist:min:max[:k=v...]",
                   action="append", dest="params", default=[])
    p.add_argument("--influence",  metavar="source:target:fn[:k=v...]",
                   action="append", dest="influences", default=[])
    p.add_argument("--limit",      type=int, default=COMBINATION_LIMIT, metavar="N")

def add_constraint_args(p):
    p.add_argument("--constraint", metavar="name:kind:param:bound",
                   action="append", dest="constraints", default=[])
    p.add_argument("--objective",  metavar="PARAM", default="demand",
                   help="param name to optimise (default: demand)")
    p.add_argument("--sense",      choices=[s.value for s in solver.Sense], default=solver.Sense.MAXIMIZE.value,
                   help="optimisation direction (default: maximize)")

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="main.py",
        description="Cartesian generator → SCIP solver pipeline with pluggable templates.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=EPILOG,
    )
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("serve",     help="persistent JSON stdio loop (frontend mode)")
    sub.add_parser("serve-api", help="start FastAPI HTTP server on port 18000")
    sub.add_parser("templates", help="list available templates")

    gen_p = sub.add_parser("generate", help="generate and print")
    add_param_args(gen_p)

    cnt_p = sub.add_parser("count",    help="print combination count only")
    add_param_args(cnt_p)

    slv_p = sub.add_parser("solve",    help="generate → solve pipeline")
    add_param_args(slv_p)
    add_constraint_args(slv_p)

    # TODO: "solve-multi" subcommand for multi-space optimisation
    # multi_p = sub.add_parser("solve-multi", help="multi-space optimisation")
    # multi_p.add_argument("--space", action="append", ...)
    # multi_p.add_argument("--global-constraint", action="append", ...)

    return p


# ── CLI Commands ──────────────────────────────────────────────────────────────
def resolve_cli_specs(args):
    """Resolve specs from --template or --param/--influence flags."""
    if args.template:
        tmpl = generator.get_template(args.template)
        return tmpl.params, tmpl.influences, tmpl.filter_fn, tmpl.name
    specs      = [parse_param(r) for r in args.params]
    influences = [parse_influence(r) for r in args.influences]
    return specs, influences, None, None

def cmd_templates(_):
    for name in generator.list_templates():
        tmpl = generator.get_template(name)
        param_names = ", ".join(p.name for p in tmpl.params)
        print(f"  {name:20s}  params: {param_names}")

def cmd_generate(args):
    specs, influences, filter_fn, template_name = resolve_cli_specs(args)
    total = total_count(*specs)

    if total > args.limit:
        print(f"WARNING: {total:,} exceeds limit of {args.limit:,}", file=sys.stderr)

    source = f"template={template_name}" if template_name else f"params={', '.join(s.name for s in specs)}"
    print(f"source:       {source}")
    print(f"combinations: {total:,}")
    print("generating...")
    items = generator.cartesian_generator(
        *specs, influences=influences, filter_fn=filter_fn, template_name=template_name)
    print(f"generated:    {len(items):,}")
    for g in items[:5]:
        print(" ", g)
    if len(items) > 5:
        print(f"  ... and {len(items) - 5:,} more")

def cmd_count(args):
    specs, _, _, _ = resolve_cli_specs(args)
    total = total_count(*specs)
    ok    = total <= args.limit
    flag  = "  !! EXCEEDS LIMIT" if not ok else ""
    print(f"combinations: {total:,}{flag}")
    print(f"limit:        {args.limit:,}")

def cmd_solve(args):
    specs, influences, filter_fn, template_name = resolve_cli_specs(args)
    total = total_count(*specs)

    if total > args.limit:
        print(f"WARNING: {total:,} exceeds limit of {args.limit:,}", file=sys.stderr)
        return

    print(f"generating {total:,} items...")
    items = generator.cartesian_generator(
        *specs, influences=influences, filter_fn=filter_fn, template_name=template_name)

    constraints = [parse_constraint(r) for r in args.constraints]
    request = solver.SolveRequest(
        items=items,
        constraints=constraints,
        objective_param=args.objective,
        objective_sense=solver.Sense(args.sense),
    )

    print(f"solving ({len(constraints)} constraints, objective={args.objective} {args.sense})...")
    result = solver.optimize(request)

    print("status:     done")
    if result.objective_value is not None:
        print(f"objective:  {result.objective_value:,.2f}")
    print(f"selected:   {len(result.selections):,} / {len(items):,}")
    for s in result.selections[:5]:
        print(" ", s)
    if len(result.selections) > 5:
        print(f"  ... and {len(result.selections) - 5:,} more")


def main(argv=None):
    parser  = build_parser()
    args    = parser.parse_args(argv)
    command = args.command

    if command == "serve":
        cmd_serve(args)
    elif command == "serve-api":
        import os
        import uvicorn
        from python.server.api import app
        host = "0.0.0.0" if os.getenv("DOCKER_CONTAINER") == "true" else "127.0.0.1"
        uvicorn.run(app, host=host, port=18000, log_level="info")
    elif command == "templates":
        cmd_templates(args)
    elif command == "generate":
        cmd_generate(args)
    elif command == "count":
        cmd_count(args)
    elif command == "solve":
        cmd_solve(args)

if __name__ == "__main__":
    main()
