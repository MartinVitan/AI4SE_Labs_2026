from pathlib import Path


def find_files(directory):
    ext = {".txt", ".eml"}
    files = []
    for p in directory.rglob("*"):
        if p.is_file() and p.suffix.lower() in ext:
            files.append(p)

    return sorted(files)


def load_file(file_path, corpus):
    try:
        t = file_path.read_text(encoding = "utf-8")
    except UnicodeError:
        raise RuntimeError()
    except OSError:
        raise RuntimeError()
    p = file_path.relative_to(corpus).as_posix()

    return {"ID": p,"path": p,"f_type": file_path.suffix.lower(),"text": t}


def compare_with_inputSources_table(documents, t_path):
    correct_p = set()
    with open(t_path, encoding = "utf-8") as t:
        next(t, None)
        for _, l in enumerate(t, start = 2):
            if not l.strip():
                continue

            col = []
            for c in l.split("|"):
                col.append(c.strip())

            if len(col) != 4:
                raise ValueError()

            p = col[2].replace("\\", "/")
            correct_p.add(p)
    d_paths = set()
    for d in documents:
        d_paths.add(d["path"].replace("\\", "/"))

    if correct_p - d_paths:
        print("V tabuľke sú súbory, ktoré sa nenačítali")
    if d_paths - correct_p:
        print("Program našiel súbory, ktoré nie sú v tabuľke")
    if not correct_p - d_paths and not d_paths - correct_p:
        print("Načítané súbory sa zhodujú s inputSources.txt")


if __name__ == "__main__":
    corpus = Path(__file__).resolve().parent / "data" / "corpus"
    if not corpus.is_dir():
        raise FileNotFoundError()
    print("input corpus dir: ", corpus)

    list_of_files = find_files(corpus)

    documents = []
    for f_p in list_of_files:
        document = load_file(f_p, corpus)
        documents.append(document)

    print("Počet načítaných dokumentov: ", len(documents))
    for d in documents:
        print(d["ID"], d["f_type"])

    t_path = Path(__file__).resolve().parent / "inputSources.txt"
    compare_with_inputSources_table(documents, t_path)