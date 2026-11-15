import json
from sentence_transformers import SentenceTransformer
from pathlib import Path


model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
model = SentenceTransformer(model_name)
embeddings_path = Path(r"Week_06_Implementation\Assignments\Task_3\embeddings.jsonl")
n = 3

def load(path, length):
    data = []
    with open(path, "r") as f:
        for l in f:
            record = json.loads(l)
            if len(record["embedding"]) != length:
                raise ValueError()
            if len(record["embedding"]) == length:
                data.append(record)
    return data


def dot_of_normalized(v1, v2):
    if len(v1) != len(v2):
        raise ValueError()
    s = 0.0
    for a, b in zip(v1, v2):
        s += a * b
    return s

def main():
    q = input("Enter query: ")
    inp_n = input("Enter value of n: ")
    val_n = 0
    if inp_n:
        try:
            val_n = int(inp_n)
        except ValueError:
            raise ValueError()
    else:
        val_n = n
    q_tokenizer = model.tokenizer
    q_tokens = q_tokenizer.backend_tokenizer.encode(q, add_special_tokens = False).ids
    q_lim = (model.max_seq_length - q_tokenizer.num_special_tokens_to_add(pair = False))
    if len(q_tokens) > q_lim:
        raise ValueError()
    q_v = model.encode(q, normalize_embeddings = True, convert_to_numpy = True)
    length = len(q_v)
    data = load(embeddings_path, length)
    scored = []
    for r in data:
        scored.append((dot_of_normalized(q_v, r["embedding"]), r))
    scored = sorted(scored, key = lambda pair: pair[0], reverse = True)
    chosen = scored[:val_n]
    for i, (score, record) in enumerate(chosen, start = 1):
        print("Podobnost: ", score)
        print("Chunk ID: ", record["chunk_id"])
        print("Index: ", record["part_idx"])
        print("Text: ", record["text"])


if __name__ == "__main__":
    main()