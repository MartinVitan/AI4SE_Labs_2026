import ast
import json
import subprocess
import sys
import textwrap
from pathlib import Path
from sentence_transformers import SentenceTransformer


task_path = Path(__file__).resolve().parent.parent / "missing_code.json"
embeddings_path = (Path(__file__).resolve().parent.parent / "Task_3" / "embeddings.jsonl")
project_root = (Path(__file__).resolve().parent.parent / "Task_1" / "AI4SE_Playground")
model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
model = SentenceTransformer(model_name)
n = 5

def load(path):
    t = json.loads(path.read_text(encoding = "utf-8"))
    if not isinstance(t, list) or not t:
        raise ValueError()
    for _, task in enumerate(t, start = 1):
        missing = {"file", "class", "method", "docstring"} - task.keys()
        if missing:
            raise ValueError()
    return t


def load_embed(path):
    data = []
    v_size = None
    with path.open("r", encoding = "utf-8") as f:
        for _, l in enumerate(f, start = 1):
            if not l.strip():
                continue
            r = json.loads(l)
            missing = {"chunk_id", "part_idx", "text", "embedding"} - r.keys()
            if missing:
                raise ValueError()
            v = r["embedding"]
            if v_size is None:
                v_size = len(v)
            elif len(v) != v_size:
                raise ValueError()
            data.append(r)
    return data, v_size


def top(q, model, records, vector_size):
    tokenizer = model.tokenizer
    q_t = tokenizer.backend_tokenizer.encode(q, add_special_tokens = False).ids
    q_limit = (model.max_seq_length - tokenizer.num_special_tokens_to_add(pair = False))
    q_v = model.encode(q,normalize_embeddings = True,convert_to_numpy = True,)

    if len(q_v) != vector_size:
        raise ValueError()

    if len(q_t) > q_limit:
        raise ValueError()
    
    scored = []
    for record in records:
        v = record["embedding"]
        if len(v) != len(q_v):
            raise ValueError()
        sum = 0
        for q_val, stored_val in zip(q_v, v):
            sum += float(q_val) * float(stored_val)
        score = sum
        scored.append((score, record))
    scored.sort(key = lambda item: item[0], reverse = True)

    return scored[:n]


def prmpt(task, source, matches):
    context = []

    for score, record in matches:
        context.append(
            "Chunk: " + str(record["chunk_id"])
            + ", part " + str(record["part_idx"])
            + ", score " + str(round(float(score), 4))
            + "\n" + record["text"])
        
    guide = ("Implementuj jednu chýbajúcu metódu Pythonu v cieľovom súbore.\n"
        "Zachovaj existujúci názov metódy, signatúru, dekorátory a docstring.\n"
        "Vráť iba telo metódy: neuvádzaj riadok def, celý súbor, vysvetlenie "
        "ani Markdownové ohraničenie kódu."
        "Použi existujúce importy projektu. Nemeň nesúvisiaci kód.\n"
        "Zdrojový súbor a nájdené chunky ber ako referenčný kontext.\n"
        "Zadanie povoľuje tieto modely: gpt-6-luna, gpt-5.6-luna, "
        "gpt-5.4-nano, gpt-5-nano, gpt-5-mini, gpt-4.1-nano, gpt-4o-mini. "
        "V novom chate vyber jeden z nich.\n")

    return (guide
        + "Úloha:\n"
        + json.dumps(task, ensure_ascii=False, indent=2)
        + "\n\nAktuálny cieľový súbor:\n"
        + source
        + "\n\nPäť najrelevantnejších nájdených chunkov:\n"
        + "\n\n".join(context))


def response():
    print("Paste method body from the chat and end with __END__ on separate line.")

    lines = []
    while True:
        l = input()
        if l.strip() == "__END__":
            break
        lines.append(l)
    return "\n".join(lines)


def find_p(s, class_name, method_name):
    tree = ast.parse(s)

    matching_classes = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            matching_classes.append(node)

    if len(matching_classes) != 1:
        raise ValueError()

    class_node = matching_classes[0]
    matching_methods = []

    for node in class_node.body:
        if (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == method_name):
            matching_methods.append(node)

    if len(matching_methods) != 1:
        raise ValueError()

    method_node = matching_methods[0]
    implementation = method_node.body

    if (implementation
        and isinstance(implementation[0], ast.Expr)
        and isinstance(implementation[0].value, ast.Constant)
        and isinstance(implementation[0].value.value, str)):
        implementation = implementation[1:]

    if (len(implementation) != 1 or not isinstance(implementation[0], ast.Pass)):
        raise ValueError()

    pass_node = implementation[0]

    if pass_node.lineno == method_node.lineno:
        raise ValueError()

    return pass_node


def replace(source, class_name, method_name, text):
    text = textwrap.dedent(text).strip("\r\n")

    if not text.strip():
        raise ValueError()
    if "```" in text:
        raise ValueError()

    wrapper = "def _generated_method():\n"
    wrapper += textwrap.indent(text, "    ")
    wrapper += "\n"
    try:
        generated_function = ast.parse(wrapper).body[0]
    except SyntaxError:
        raise ValueError()

    has_nested_definition = False

    for node in generated_function.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            has_nested_definition = True
            break

    if has_nested_definition:
        raise ValueError()

    if (len(generated_function.body) == 1 and isinstance(generated_function.body[0], ast.Pass)):
        raise ValueError() 

    pass_node = find_p(source, class_name, method_name)
    source_lines = source.splitlines(keepends = True)
    indentation = " " * pass_node.col_offset
    newline = "\r\n" if "\r\n" in source else "\n"

    replacement_lines = []

    for line in text.splitlines():
        if line.strip():
            replacement_lines.append(indentation + line + newline)
        else:
            replacement_lines.append(newline)

    start = pass_node.lineno - 1
    end = pass_node.end_lineno or pass_node.lineno
    source_lines[start:end] = replacement_lines
    updated_source = "".join(source_lines)
    ast.parse(updated_source)

    return updated_source


def target_path(task):
    relative_path = Path(task["file"])

    if relative_path.is_absolute():
        raise ValueError()

    root = project_root.resolve()
    target = (project_root / relative_path).resolve()

    try:
        target.relative_to(root)
    except ValueError:
        raise ValueError()

    if not target.is_file():
        raise FileNotFoundError()

    return target


def prepare(tasks, data, v_size):
    updated_s = {}
    for index, task in enumerate(tasks, start = 1):
        path = target_path(task)
        s = updated_s.get(path)
        if s is None:
            s = path.read_text(encoding="utf-8")
        find_p(s, task["class"], task["method"])
        query = (
            task["class"] + "." + task["method"]
            + " in " + task["file"] + ": "
            + task["docstring"]
        )
        matches = top(query, model, data, v_size)
        prompt = prmpt(task, s, matches)

        print(" Task " + str(index) + "/" + str(len(tasks)) + " ")
        print("Copy this prompt into a new chat using an allowed model:\n")
        print(prompt)

        input("\nAfter receiving the chat response, press Enter to paste it here.")
        body = response()
        updated_s[path] = replace(s, task["class"], task["method"], body)

        print("Prepared and syntax-checked " + task["class"] + "." + task["method"] + ".")

    return updated_s


def tst():
    tests_dir = project_root / "playground"
    if not tests_dir.is_dir():
        raise FileNotFoundError()

    command = [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        "tests",
        "-v"]

    result = subprocess.run(
        command,
        cwd = tests_dir,
        capture_output = True,
        text = True,
        check = False)

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    print(result.returncode)
    return result.returncode


def main():
    tasks = load(task_path)
    records, vector_size = load_embed(embeddings_path)
    updated_sources = prepare(tasks, records, vector_size)
    for path in updated_sources:
        print(f"- {path.relative_to(project_root.resolve())}")
    confirmation = input("\nWrite these changes and run tests? y/n: ").strip().lower()
    if confirmation not in {"y"}:
        return 0
    for path, source in updated_sources.items():
        path.write_text(source, encoding = "utf-8")
    return tst()


if __name__ == "__main__":
    main()