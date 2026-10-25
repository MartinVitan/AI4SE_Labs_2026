import json
from openai import OpenAI
from pathlib import Path


m = "gpt-5.6-luna"

def zjednot_davku_kandidatov(candidates, a):
    model_input = []
    for candidate in candidates:
        candidate_ids = candidate.get("candidate_ids")
        if candidate_ids is None:
            candidate_ids = [candidate["candidate_id"]]
        model_input.append({"candidate_ids": candidate_ids,"candidate_text": candidate["candidate_text"],"kind": candidate["kind"]})
    c_json = json.dumps(model_input, ensure_ascii = False, indent = 2)
    p = ("Zoskup kandidátov, ktorí popisujú tú istú potrebu a majú rovnaký význam. "
         "Podobnosť tém dvoch požiadaviek nie je postačujúca na ich zlučenie. "
         "Zachovaj rozdiely v typoch požiadavok. (otázka, ...) "
         "Nevymýšlaj nové informácie. "
         "Zahrň každý vstupný candidate_id práve raz. "
         "Nevytváraj nové candidate_id ani žiaden nevynechaj. "
         "Vráť iba JSON objekt v tomto tvare: "
        '{"candidates": ['
        '{"candidate_text": "zjednotený opis kandidátnej požiadavky", '
        '"kind": "requirement, proposal alebo open_question", '
        '"uncertainties": [], '
        '"candidate_ids": ["existujúce ID kandidáta"]}'
        "]}\n"
        "V tomto kroku neistoty nevyhodnocuj ani nerieš. Vo výstupnom poli uncertainties vráť prázdny zoznam. "
        "Dôkazy nevytváraj ani nekopíruj. dopln ich program z pôvodných kandidátov. "
        "candidate_id používaj iba ak sa nachádzajú vo vstupných dátach. "
        "Vstupní kandidáti:\n" + c_json)
    created_response = a.chat.completions.create( model = m, messages = [ { "role": "user", "content": p } ], response_format={"type": "json_object"} )
    o = created_response.choices[0].message.content
    odpoved = json.loads(o)
    return odpoved["candidates"]


def zjednot_kandidatov(candidates, a):
    batch_size = 20
    original_by_id = {}

    for candidate in candidates:
        original_by_id[candidate["candidate_id"]] = candidate

    batch_results = []

    for start in range(0, len(candidates), batch_size):
        batch = candidates[start:start + batch_size]
        batch_results.extend(zjednot_davku_kandidatov(batch, a))

    if len(batch_results) > 1:
        o_candidates = zjednot_davku_kandidatov(batch_results, a)
    else:
        o_candidates = batch_results
    used_ids = set()
    for n, candidate in enumerate(o_candidates, start = 1):
        source_paths = []
        evidence = []
        for candidate_id in candidate["candidate_ids"]:
            used_ids.add(candidate_id)
            original = original_by_id[candidate_id]
            source_path = original.get("source_path")
            if source_path and source_path not in source_paths:
                source_paths.append(source_path)
            evidence.append({"candidate_id": candidate_id,"source_path": source_path,"evidence": original.get("evidence", "")})

        candidate["normalized_id"] = "N" + str(n).zfill(3)
        candidate["source_paths"] = source_paths
        candidate["evidence"] = evidence
    missing_ids = set(original_by_id) - used_ids
    missing_candidates = []

    for candidate_id in sorted(missing_ids):
        missing_candidates.append(original_by_id[candidate_id])

    return o_candidates, missing_candidates


if __name__ == "__main__":
    a = OpenAI()
    directory = Path(__file__).resolve().parent
    input_path = directory / "elicitation_candidates.json"
    o_path = directory / "zjednotene_requirements.json"
    with open(input_path, "r", encoding = "utf-8") as f:
        input_data = json.load(f)
    candidates = input_data["candidates"]
    zjednotene, missing_candidates = zjednot_kandidatov(candidates, a)
    with open(o_path, "w", encoding = "utf-8") as output_file:
        json.dump({"candidates": zjednotene,"missing_candidates": missing_candidates}, output_file, ensure_ascii = False, indent = 2)