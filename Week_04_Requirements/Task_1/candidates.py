import json
from openai import OpenAI
from load import find_files, load_file
from pathlib import Path


m = "gpt-6-luna"

def choose_cand(document, a):
    p = ("Z dokumentu vyber kandidátne softvérové požiadavky. "
         "Zahrň požiadavky, návrhy a otázky, ktoré sa týjakú systému. "
         "Nezahŕňaj nič iné ani žiaden nesúviciaci text. Chýbajúce informácie nedopĺňaj. "
         "Vráť JSON objekt v tomto tvare: "
         '{"candidates": ['
        '{"candidate_text": "opis", '
        '"evidence": "úryvok zo zdroja (doslovný)", '
        '"kind": "requirement, proposal alebo open_question", '
        '"uncertainties": []}'
        "]}"
        "Text dokumentu: " + document["text"])
    created_response = a.chat.completions.create( model = m, messages = [ { "role": "user", "content": p } ], response_format = {"type": "json_object"} )
    o = created_response.choices[0].message.content
    odpoved = json.loads(o)
    cand = odpoved["candidates"]
    for n, candidate in enumerate(cand, start = 1):
        candidate["candidate_id"] = (document["ID"] + "::C" + str(n))
        candidate["source_path"] = document["path"]
    return cand

if __name__ == "__main__":
    a = OpenAI()
    corpus = Path(__file__).resolve().parent / "data" / "corpus"
    if not corpus.is_dir():
        raise FileNotFoundError()
    f = find_files(corpus)
    if not f:
        raise FileNotFoundError()
    candidates = []
    for n, f_p in enumerate(f, start = 1):
        document = load_file(f_p, corpus)
        c = choose_cand(document, a)
        candidates.extend(c)
    with open(Path(__file__).resolve().parent / "elicitation_candidates.json", "w", encoding = "utf-8") as out:
        json.dump({ "candidates": candidates }, out, ensure_ascii = False, indent = 2)