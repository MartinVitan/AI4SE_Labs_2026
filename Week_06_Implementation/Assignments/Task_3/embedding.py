from sentence_transformers import SentenceTransformer
from pathlib import Path
import json


model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
model = SentenceTransformer(model_name)
chunks_path = Path(r"Week_06_Implementation\Assignments\Task_2\chunks.jsonl")
embeddings_path = Path(r"Week_06_Implementation\Assignments\Task_3\embeddings.jsonl")
overlap = 16
batch_sz = 16

def parts(text, tokenizer, max_len):
    limit = max_len - tokenizer.num_special_tokens_to_add(pair = False)
    over = min(overlap, limit - 1)
    out = []
    tokens = tokenizer.backend_tokenizer.encode(text, add_special_tokens = False).ids
    step = limit - over
    for x in range(0, len(tokens), step):
        y = min(x + limit, len(tokens))
        part_txt = tokenizer.decode(tokens[x:y], skip_special_tokens = True, clean_up_tokenization_spaces = False)
        if len(tokenizer.backend_tokenizer.encode(part_txt, add_special_tokens = True).ids) > max_len:
            raise ValueError()
        out.append({"token_start": x, "token_end": y, "text": part_txt})
    return out


def main():
    ch = []
    with open(chunks_path, "r", encoding = "utf-8") as f:
        for _, l in enumerate(f, start = 1):
            if not l.strip():
                continue
            chunk = json.loads(l)
            ch.append(chunk)
    metadata = []
    for _, chunk in enumerate(ch, start = 1):
        p = parts(chunk["text"], model.tokenizer, model.max_seq_length)
        for i, part in enumerate(p, start = 1):
            metadata.append({
                "chunk_id": chunk['path'] + "_" + str(chunk['start_l']) + "_" + str(chunk['end_l']),
                "part_idx": i,
                "parts": len(p),
                "token_start": part["token_start"],
                "token_end": part["token_end"],
                "text": part["text"]
            })
    texts = []
    for r in metadata:
        texts.append(r["text"])
    vectors = model.encode(texts, batch_size = batch_sz, normalize_embeddings = True, convert_to_numpy = True, show_progress_bar = True,)
    if len(vectors) != len(metadata):
        raise RuntimeError()
    with open(embeddings_path, "w", encoding = "utf-8") as f:
        for r, v in zip(metadata, vectors):
            r["embedding"] = v.tolist()
            f.write(json.dumps(r, ensure_ascii = False) + "\n")
    
    print("Output file: ", embeddings_path)


if __name__ == "__main__":
    main()