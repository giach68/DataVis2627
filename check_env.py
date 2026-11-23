import ast, json, sys, pathlib
from importlib.metadata import packages_distributions, distributions

root = pathlib.Path(".")
stdlib = set(sys.stdlib_module_names)
imports = set()

for f in root.rglob("*"):
    if ".venv" in f.parts:
        continue
    code = ""
    if f.suffix == ".py":
        code = f.read_text(encoding="utf-8", errors="ignore")
    elif f.suffix == ".ipynb":
        nb = json.loads(f.read_text(encoding="utf-8"))
        code = "\n".join("".join(c["source"]) for c in nb["cells"]
                         if c["cell_type"] == "code"
                         and not "".join(c["source"]).lstrip().startswith(("%", "!")))
    try:
        for n in ast.walk(ast.parse(code)):
            if isinstance(n, ast.Import):
                imports |= {a.name.split(".")[0] for a in n.names}
            elif isinstance(n, ast.ImportFrom) and n.module and n.level == 0:
                imports.add(n.module.split(".")[0])
    except SyntaxError:
        pass

imports -= stdlib
dist_map = packages_distributions()
needed = set()
for m in sorted(imports):
    if m in dist_map:
        needed |= set(dist_map[m])
    else:
        print(f"NON INSTALLATO nel venv: {m}")

req_file = root / "requirements.txt"
reqs = set()
if req_file.exists():
    for line in req_file.read_text().splitlines():
        line = line.split("#")[0].strip()
        if line and not line.startswith("-"):
            name = line.split("==")[0].split(">")[0].split("<")[0].split("[")[0].strip()
            reqs.add(name.lower().replace("_", "-"))
else:
    print("requirements.txt NON TROVATO")

norm = {d.lower().replace("_", "-") for d in needed}
print("\nUsati dal codice ma assenti da requirements.txt:", sorted(norm - reqs) or "nessuno")
print("In requirements.txt ma non importati direttamente:", sorted(reqs - norm) or "nessuno")