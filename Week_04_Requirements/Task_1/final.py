import json
from pathlib import Path
from openai import OpenAI

m = "gpt-5.6-luna"
batch_size = 10

def prepare_batch(candidates, client):
    batch_input = []
    for candidate in candidates:
        batch_input.append({"normalized_id": candidate["normalized_id"],"kind": candidate.get("kind", "requirement"),"candidate_text": candidate.get("candidate_text", ""),"evidence": candidate.get("evidence", [])})

        p = (
        "Priprav štruktúrované položky pre dokument softvérových "
        "požiadaviek v slovenčine. Pre každú vstupnú položku vráť "
        "presne jednu položku. Zachovaj jej význam a typ. Nevymýšľaj "
        "fakty ani požiadavky. Každá položka má mať krátky výstižný "
        "názov a vysvetlenie v jednom odseku približne 2 až 4 vety. "
        "Vyhodnoť prioritu podľa dôkazov: HIGH pre jasne vysoký dopad "
        "alebo naliehavosť, LOW pre jasne malý dopad a MEDIUM ako "
        "predvolenú prioritu pre bežnú požiadavku alebo návrh. "
        "UNASSIGNED použi iba pre open_question alebo ak chýbajú "
        "informácie na určenie priority. Vráť iba JSON objekt v tomto "
        "tvare:\n"
        '{"items": [{"normalized_id": "ID zo vstupu", '
        '"name": "Krátky názov", '
        '"explanation": "Odsek s vysvetlením", '
        '"priority": "HIGH"}]}\n\n'
        "Vstupné položky:\n"
        + json.dumps(batch_input, ensure_ascii=False, indent=2)
        )

    response = client.chat.completions.create(model = m,messages=[{"role": "user", "content": p}],response_format={"type": "json_object"})
    response_text = response.choices[0].message.content
    result = json.loads(response_text)
    generated_items = result.get("items")
    expected_ids = set()
    for candidate in candidates:
        expected_ids.add(candidate["normalized_id"])
    generated_id = {}
    for i in generated_items:
        normalized_id = i.get("normalized_id")
        generated_id[normalized_id] = i
    final_items = []
    for candidate in candidates:
        normalized_id = candidate["normalized_id"]
        generated = generated_id[normalized_id]
        sources = candidate.get("source_paths", [])
        if not isinstance(sources, list):
            sources = []
        if not sources:
            evidence = candidate.get("evidence", [])
            if isinstance(evidence, list):
                for evidence_item in evidence:
                    if not isinstance(evidence_item, dict):
                        continue
                    source_path = evidence_item.get("source_path")
                    if isinstance(source_path, str) and source_path not in sources:
                        sources.append(source_path)
        final_items.append({
            "id": normalized_id,
            "name": generated["name"].strip(),
            "explanation": generated["explanation"].strip(),
            "priority": generated["priority"],
            "kind": candidate.get("kind", "requirement"),
            "candidate_ids": candidate.get("candidate_ids", []),
            "source_documents": sources,
            "evidence": candidate.get("evidence", [])})
    return final_items

if __name__ == "__main__":
    directory = Path(__file__).resolve().parent
    input_path = directory / "requirements_after_step5.json"
    report_path = directory / "oprava_report.json"
    output_path = directory / "final_requirements.json"

    with open(input_path, "r", encoding="utf-8") as input_file:
        input_data = json.load(input_file)

    with open(report_path, "r", encoding="utf-8") as input_file:
        repair_report = json.load(input_file)

    candidates = input_data.get("candidates")

    seen_ids = set()
    for candidate in candidates:
        normalized_id = candidate.get("normalized_id")
        seen_ids.add(normalized_id)

    a = OpenAI()
    final_items = []
    for start in range(0, len(candidates), batch_size):
        batch = candidates[start:start + batch_size]
        final_items.extend(prepare_batch(batch, a))
    requirements = []
    proposals = []
    open_questions = []
    other_items = []
    for item in final_items:
        if item["kind"] == "requirement":
            requirements.append(item)
        elif item["kind"] == "proposal":
            proposals.append(item)
        elif item["kind"] == "open_question":
            open_questions.append(item)
        else:
            other_items.append(item)

    document = {
        "title": "Dokument softvérových požiadaviek",
        "priority_scale": {
            "HIGH": "Kritická alebo vysoko naliehavá položka s veľkým dopadom podľa vstupných dôkazov",
            "MEDIUM": "Bežná funkčná požiadavka alebo návrh",
            "LOW": "Voliteľné zlepšenie alebo položka s malým dopadom",
            "UNASSIGNED": "Otvorená otázka alebo nedostatok dôkazov",
        },
        "requirements": requirements,
        "proposals": proposals,
        "open_questions": open_questions,
        "other_items": other_items,
        "blacklist": [],
        "unresolved_review_issues": repair_report.get(
            "unresolved_issues",
            [],
        ),
    }

    with open(output_path, "w", encoding="utf-8") as output_file:
        json.dump(document, output_file, ensure_ascii=False, indent=2)