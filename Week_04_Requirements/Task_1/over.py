import json
from openai import OpenAI
from pathlib import Path


m = "gpt-5.4-nano"
batch_size = 10


def review(candidates, zjednoteny_candidates, a):
    original_json = json.dumps(candidates, ensure_ascii = False, indent = 2) 
    zjednotene_json = json.dumps(zjednoteny_candidates, ensure_ascii = False, indent = 2)
    p = ("Skontroluj pôvodných kandidátov a zjednotených kandidátov."
        "Hľadaj iba problémy podložené vstupnými dátami: "
        "nejasnú alebo nedostatočne konkrétnu formuláciu, "
        "zjednotenie kandidátov, ktorí nemajú rovnaký význam, "
        "možné rozpory medzi zjednotenými položkami, "
        "požiadavku, návrh alebo otázku, ktorej význam sa pri zjednotení zmenil, "
        "dôležitý detail alebo podmienku, ktorá sa pri zjednotení stratila"
        "Nevymýšľaj chýbajúce požiadavky ani fakty."
        "Nerob opravy a neprideľuj priority."
        "Ak problém nevieš potvrdiť, označ ho ako uncertain a vysvetli."
        "Každý problém musí uvádzať affected_ids:"
        "použi normalized_id alebo candidate_id, ktoré sú vo vstupných dátach."
        "Ak problém nenájdeš, vráť prázdny zoznam"
        "Vráť iba JSON objekt v tomto tvare:\n"
        '{"issues": ['
        '"issue_type": "ambiguity, possible_conflict, bad_merge, '
        'lost_detail alebo uncertainty", '
        '"affected_ids": ["ID zo vstupných dát"], '
        '"explanation": "čo je problém a na základe čoho", '
        '"suggested_action": "čo treba preveriť alebo opraviť"}'
        "]}"
        "Pôvodní kandidáti:\n" + original_json + "\n\nZjednotené položky:\n" + zjednotene_json)
    odpoved = a.chat.completions.create( model = m, messages = [ { "role": "user", "content": p } ], response_format = {"type": "json_object"} )
    o_text = odpoved.choices[0].message.content
    o = json.loads(o_text)
    return o["issues"]


if __name__ == "__main__":
    a = OpenAI()
    directory = Path(__file__).resolve().parent
    input_path = directory / "elicitation_candidates.json"
    zjednotene_path = directory / "zjednotene_requirements.json"
    output_path = directory / "report.json"
    with open(input_path, "r", encoding = "utf-8") as i_f:
        orig_data = json.load(i_f)
    with open(zjednotene_path, "r", encoding = "utf-8") as i_f:
        zjed_data = json.load(i_f)
    orig_candidates = orig_data["candidates"]
    zjed_candidates = zjed_data["candidates"]
    o_by_id = {}
    for c in orig_candidates: 
        o_by_id[c["candidate_id"]] = c
    used_ids = set()
    for c in zjed_candidates: 
        for c_id in c.get("candidate_ids", []):
            used_ids.add(c_id)
    missing_c = []
    missing = set(o_by_id) - used_ids
    for c_id in sorted(missing):
        missing_c.append(o_by_id[c_id])
    issues = []
    for start in range(0, len(zjed_candidates), batch_size):
        batch = zjed_candidates[start:start + batch_size]
        related = set()
        for c in batch:
            related.update(c.get("candidate_ids", []))
        o_batch = []
        for c in sorted(related):
            if c in o_by_id:
                o_batch.append(o_by_id[c])
        i = review(o_batch, batch, a)
        issues.extend(i)
    for start in range(0, len(missing_c), batch_size):
        m_batch = missing_c[start:start + batch_size]
        i = review(m_batch, [], a)
        issues.extend(i)
    report = { "missing_candidate_ids": sorted(missing), "missing_candidates": missing_c, "issues": issues }
    with open(output_path, "w", encoding = "utf-8") as o_f:
        json.dump(report, o_f, ensure_ascii = False, indent = 2)
    print("# pôvodných kandidátov: ", len(orig_candidates)) 
    print("# zjednotených: ", len(zjed_candidates)) 
    print("# vynechaných kandidátov: ", len(missing_c))
    print("# nálezov issues: ", len(issues))