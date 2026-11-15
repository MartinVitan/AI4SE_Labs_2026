from pathlib import Path
import os
import json


repozitar = Path("Week_06_Implementation/Assignments/Task_1/AI4SE_Playground")
out = Path(__file__).with_name("chunks.jsonl")
out.write_text("", encoding = "utf-8")
for f in repozitar.rglob("*"):
    if f.is_file() and not f.suffix in [".exe", ".bin"] and not f.name.startswith("."):
        with open(f, "r", encoding = "utf-8") as file:
            l = file.readlines()
            chunk_size = 50
            for n in range(len(l)):
                if n % chunk_size == 0:
                    chunk = l[n: n + chunk_size]
                    text = ""
                    for r in chunk:
                        text += r
                    contains = {"path": str(f), "start_l": n + 1, "end_l": n + len(chunk), "text": text}
                    json_data = json.dumps(contains, ensure_ascii = False)
                    with open(out, "a", encoding = "utf-8") as out_file:
                        out_file.write(json_data + "\n")