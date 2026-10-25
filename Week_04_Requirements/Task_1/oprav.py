import json
from pathlib import Path
from openai import OpenAI
from langgraph.graph import END, START, MessagesState, StateGraph
from over import review


m = "gpt-5.6-luna"
batch_size = 10


def load_state(state):
    messages = state.get("messages", [])
    message = messages[-1]
    if isinstance(message, dict):
        content = message.get("content")
    else:
        content = message.content
    return json.loads(content)


def save_state(data):
    return {
        "messages": [{
            "role": "user",
            "id": "workflow-state",
            "content": json.dumps(data, ensure_ascii=False),
        }]
    }


def c_ids(cand):
    ids = cand.get("candidate_ids", [])
    result = []
    for c_id in ids:
        if isinstance(c_id, str):
            result.append(c_id)
    return result


def missing(orig_c, zjed_c):
    used_ids = set()
    for c in zjed_c:
        used_ids.update(c_ids(c))
    miss = []
    for c in orig_c:
        c_id = c.get("candidate_id")
        if c_id not in used_ids:
            miss.append(c)
    return miss


def back_missing(miss_c, zjed_c):
    opr = []
    for c in zjed_c:
        opr.append(dict(c))

    used_normalized_ids = set()
    for c in opr:
        normalized_id = c.get("normalized_id")
        if isinstance(normalized_id, str):
            used_normalized_ids.add(normalized_id)

    for c in miss_c:
        c_id = c.get("candidate_id")
        restored = dict(c)
        restored["normalized_id"] = c_id
        restored["candidate_ids"] = [c_id]
        source_path = c.get("source_path")
        if isinstance(source_path, str):
            restored["source_paths"] = [source_path]
        elif not isinstance(c.get("source_paths"), list):
            restored["source_paths"] = []
        restored["recovered"] = True
        opr.append(restored)
        used_normalized_ids.add(c_id)
    return opr


def prep_batches(orig_c, zjed_c, issues):
    orig_id = {}
    for c in orig_c:
        candidate_id = c.get("candidate_id")
        if isinstance(candidate_id, str):
            orig_id[candidate_id] = c
    normalized_by_id = {}
    candidate_to_normalized = {}
    for c in zjed_c:
        n_id = c.get("normalized_id")

        normalized_by_id[n_id] = c

        for candidate_id in c_ids(c):
            candidate_to_normalized[candidate_id] = c

    grps = {}

    for issue in issues:
        if not isinstance(issue, dict):
            continue
        affected_ids = issue.get("affected_ids", [])
        if not isinstance(affected_ids, list):
            continue
        for a_id in affected_ids:
            if not isinstance(a_id, str):
                continue

            c = normalized_by_id.get(a_id)
            if c is None:
                c = candidate_to_normalized.get(a_id)
            if c is None:
                continue

            n_id = c["normalized_id"]

            if n_id not in grps:
                grps[n_id] = {"candidate": c,"issues": [],"original_candidates": [],}
            group = grps[n_id]
            if issue not in group["issues"]:
                group["issues"].append(issue)
            for candidate_id in c_ids(c):
                original = orig_id.get(candidate_id)
                if (original is not None and original not in group["original_candidates"]):
                    group["original_candidates"].append(original)

    all_groups = list(grps.values())
    batches = []
    for start in range(0, len(all_groups), batch_size):
        batches.append(all_groups[start:start + batch_size])
    return batches


def repair_batch(batch, a):
    r_input = []
    for g in batch:
        c = g["candidate"]
        text_field = None
        for f in ("candidate_text", "requirement_text", "text"):
            val = c.get(f)
            if isinstance(val, str) and val.strip():
                text_field = f
                break

        r_input.append({
            "normalized_id": c["normalized_id"],
            "text_field": text_field,
            "current_text": c[text_field],
            "candidate_ids": c_ids(c),
            "source_paths": c.get("source_paths", []),
            "evidence": c.get("evidence", []),
            "original_candidates": g["original_candidates"],
            "issues": g["issues"],
        })

    p = ("Navrhni opravy textov zjednotených položiek. "
        "Použi iba pôvodných kandidátov, dôkazy a uvedené nálezy. "
        "Nevymýšľaj nové požiadavky. Zachovaj význam, podmienky "
        "a dôležité detaily. Nemeň normalized_id, candidate_ids, "
        "source_paths ani evidence. Ak sa problém nedá bezpečne "
        "opraviť úpravou textu, pre danú položku nevracaj opravu. "
        "Vráť iba JSON objekt v tomto tvare:\n"
        '{"revisions": [{"normalized_id": "ID položky", '
        '"revised_text": "Navrhnutý opravený text"}]}\n\n'
        "Položky:\n" + json.dumps(r_input, ensure_ascii = False, indent = 2))

    response = a.chat.completions.create(model = m, messages=[{"role": "user", "content": p}], response_format = {"type": "json_object"})
    response_text = response.choices[0].message.content
    result = json.loads(response_text)
    revisions = result.get("revisions")

    allowed_ids = set()
    for g in batch:
        allowed_ids.add(g["candidate"]["normalized_id"])
    return revisions


def rew(state):
    data = load_state(state)
    orig_c, zjed_c = data["orig_c"], data["zjed_c"]
    orig_id = {}
    for c in orig_c:
        candidate_id = c.get("candidate_id")
        if isinstance(candidate_id, str):
            orig_id[candidate_id] = c
    a = OpenAI()
    issues = []
    for start in range(0, len(zjed_c), batch_size):
        b = zjed_c[start:start + batch_size]
        related_ids = set()
        for c in b:
            related_ids.update(c_ids(c))
        orig_b = []
        for candidate_id in sorted(related_ids):
            orig = orig_id.get(candidate_id)
            if orig is not None:
                orig_b.append(orig)
        batch_issues = review(orig_b, b, a)
        issues.extend(batch_issues)
    missing_c = missing(orig_c, zjed_c)
    miss_ids = []
    for c in missing_c:
        miss_ids.append(c["candidate_id"])
    hist = list(data["issue_history"])
    hist.append({"repair_r": data["repair_r"], "missing_candidate_ids": miss_ids, "issues": issues,})
    data["issues"] = issues
    data["missing_ids"] = miss_ids
    data["issue_history"] = hist
    return save_state(data)


def rep(state):
    data = load_state(state)
    orig_c, zjed_c = data["orig_c"], data["zjed_c"]
    missing_candidates = missing(orig_c, zjed_c)
    zjed_c = back_missing(missing_candidates, zjed_c)
    batches = prep_batches(orig_c, zjed_c, data["issues"])
    revisions = []

    if batches:
        a = OpenAI()
        for b in batches:
            revisions.extend(repair_batch(b, a))

    candidates_id = {}
    for c in zjed_c:
        n_id = c.get("normalized_id")
        candidates_id[n_id] = dict(c)
    for revision in revisions:
        n_id = revision["normalized_id"]
        c = candidates_id[n_id]
        text_f = None
        for f in ("candidate_text", "requirement_text", "text"):
            value = c.get(f)
            if isinstance(value, str) and value.strip():
                text_f = f
                break
        c[text_f] = revision["revised_text"].strip()
    updated_zjed_c = []
    for c in zjed_c:
        updated_zjed_c.append(candidates_id[c["normalized_id"]])
    data["zjed_c"] = updated_zjed_c
    data["repair_r"] += 1
    return save_state(data)


def final(state):
    data = load_state(state)
    output_dir = Path(data["directory"])
    remaining_miss = missing(data["orig_c"], data["zjed_c"])
    remaining_missing_ids = []
    for c in remaining_miss:
        remaining_missing_ids.append(c["candidate_id"])
    req_path = output_dir / "requirements_after_step5.json"
    rep_path = output_dir / "oprava_report.json"
    requirements_data = {"candidates": data["zjed_c"]}
    report_data = {"repair_r": data["repair_r"],"remaining_missing_candidate_ids": remaining_missing_ids,"unresolved_issues": data["issues"],"issue_history": data["issue_history"]}
    with open(req_path, "w", encoding="utf-8") as o_f:
        json.dump(requirements_data, o_f, ensure_ascii = False, indent = 2)
    with open(rep_path, "w", encoding="utf-8") as o_f:
        json.dump(report_data, o_f, ensure_ascii = False, indent = 2)
    return save_state(data)

def c_graph():
    graph = StateGraph(MessagesState)
    graph.add_node("rep", rep)
    graph.add_node("rew", rew)
    graph.add_node("final", final)
    graph.add_edge(START, "rep")
    graph.add_edge("rep", "rew")
    graph.add_conditional_edges(
        "rew",
        lambda state: ("final"
            if ((data := load_state(state))["repair_r"] >= 2 or (not data["issues"] and not data["missing_ids"]))
            else "rep"),
        {"rep": "rep", "final": "final",})
    graph.add_edge("final", END)
    return graph.compile()


if __name__ == "__main__":
    directory = Path(__file__).resolve().parent
    orig_path = directory / "elicitation_candidates.json"
    zjed_path = directory / "zjednotene_requirements.json"
    report_path = directory / "report.json"
    with open(orig_path, "r", encoding = "utf-8") as i_f:
        orig_data = json.load(i_f)
    with open(zjed_path, "r", encoding = "utf-8") as i_f:
        zjed_data = json.load(i_f)
    with open(report_path, "r", encoding = "utf-8") as i_f:
        report_data = json.load(i_f)
    orig_c = orig_data.get("candidates")
    zjed_c = zjed_data.get("candidates")
    issues = report_data.get("issues", [])
    missing_c = missing(orig_c, zjed_c)
    missing_ids = []
    for c in missing_c:
        missing_ids.append(c["candidate_id"])
    init_data = {
        "orig_c": orig_c,
        "zjed_c": zjed_c,
        "issues": issues,
        "missing_ids": missing_ids,
        "repair_r": 0,
        "issue_history": [{
            "repair_r": 0,
            "missing_candidate_ids": missing_ids,
            "issues": issues}],
        "directory": str(directory)}
    app = c_graph()
    app.invoke({
        "messages": [{
            "role": "user",
            "id": "workflow-state",
            "content": json.dumps(init_data, ensure_ascii=False)}]})