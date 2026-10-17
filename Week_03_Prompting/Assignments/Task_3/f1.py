import csv
import importlib.util
import json
import sqlite3
from collections import Counter
from pathlib import Path


TASK2_DIR = Path(__file__).resolve().parent.parent / "Task_2"
DATA_DIR = TASK2_DIR / "data"
LABELS_PATH = DATA_DIR / "restaurants_dataset.csv"
EVALUATOR_PATH = DATA_DIR / "evaluate_retrieval_predictions.py"
DEFAULT_PREDICTIONS = {
    "RACE": TASK2_DIR / "RACEout.txt",
    "RTF": TASK2_DIR / "RTFout.txt",
    "CO-STAR": TASK2_DIR / "COSTARout.txt",
}


def load_db():
    spec = importlib.util.spec_from_file_location("task2_evaluator", EVALUATOR_PATH)
    if spec is None or spec.loader is None:
        raise ImportError()
    evaluator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(evaluator)
    return evaluator.load_database()


def load_lbl(labels_path): #priprava zoznamu spravnych odpovedi na otazky
    labels_by_q = {}
    csv.field_size_limit(1_000_000_000)

    with labels_path.open(encoding = "utf-8", newline = "") as source:
        reader = csv.DictReader(source)
        columns = reader.fieldnames or []
        if "question" not in columns or "result" not in columns:
            raise ValueError()

        for l, row in enumerate(reader, start=2):
            try:
                result = json.loads(row["result"])
            except json.JSONDecodeError as error:
                raise ValueError() from error

            if not isinstance(result, list):
                raise ValueError()

            names = []
            for label in result:
                if (isinstance(label, list) and len(label) >= 2 and isinstance(label[1], str)):
                    names.append(label[1])
                else:
                    raise ValueError()

            question = row["question"]
            if question not in labels_by_q:
                labels_by_q[question] = []
            labels_by_q[question].append(Counter(names))
    return labels_by_q


def calc_q_scores(expected_names, predicted_names): #skore jednej otazky teda TP, FP, FN -> precision, recall -> F1
    true_positives = sum((expected_names & predicted_names).values())
    false_positives = sum((predicted_names - expected_names).values())
    false_negatives = sum((expected_names - predicted_names).values())

    predicted_count = true_positives + false_positives
    expected_count = true_positives + false_negatives

    precision = true_positives / predicted_count if predicted_count else 0.0
    recall = true_positives / expected_count if expected_count else 0.0

    f1_formula_total = 2 * true_positives + false_positives + false_negatives
    if f1_formula_total == 0:
        f1 = 1.0
    else:
        f1 = 2 * true_positives / f1_formula_total

    return precision, recall, f1


def eval_pred(predictions_path, labels_path, connection): #vyhodnotenie jedneho outputu frameworku, uloženie skóre otázky, každá otázka rovnaká váha
    labels_by_question = load_lbl(labels_path)
    precision_scores = []
    recall_scores = []
    f1_scores = []

    with predictions_path.open(encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        columns = reader.fieldnames or []
        if "question" not in columns:
            raise ValueError()
        if "predicted_sql" in columns:
            sql_column = "predicted_sql"
        elif "sql" in columns:
            sql_column = "sql"
        else:
            raise ValueError()

        for l, row in enumerate(reader, start=2):
            question = row["question"]
            if question in labels_by_question and len(labels_by_question[question]) > 0:
                expected_names = labels_by_question[question].pop(0)
            else:
                raise ValueError()

            try:
                query = connection.execute(row[sql_column])
                predicted_rows = query.fetchall()
            except sqlite3.Error as error:
                raise RuntimeError() from error

            name_column_index = None
            for index, column in enumerate(query.description or []):
                if column[0].casefold() == "name":
                    name_column_index = index
                    break

            if predicted_rows and name_column_index is None:
                raise ValueError()
            if name_column_index is None:
                predicted_names = Counter()
            else:
                predicted_names = Counter(result_row[name_column_index] for result_row in predicted_rows)

            precision, recall, f1 = calc_q_scores(expected_names, predicted_names)
            precision_scores.append(precision)
            recall_scores.append(recall)
            f1_scores.append(f1)

    unmatched_labels = sum(len(results) for results in labels_by_question.values())
    if unmatched_labels > 0:
        raise ValueError()
    if len(f1_scores) == 0:
        raise ValueError()

    question_count = len(f1_scores)
    return {
        "questions": question_count,
        "precision": sum(precision_scores) / question_count,
        "recall": sum(recall_scores) / question_count,
        "f1": sum(f1_scores) / question_count,
    }


def main():
    connection = load_db()
    try:
        for prompt_name, predictions_path in DEFAULT_PREDICTIONS.items():
            scores = eval_pred(
                predictions_path, LABELS_PATH, connection
            )
            precision = str(round(scores["precision"] * 100, 2)) + "%"
            recall = str(round(scores["recall"] * 100, 2)) + "%"
            f1 = str(round(scores["f1"] * 100, 2)) + "%"
            print(
                prompt_name
                + ": Precision "
                + precision
                + ", Recall "
                + recall
                + ", macro F1 "
                + f1
                + " ("
                + str(scores["questions"])
                + " questions)"
            )
    finally:
        connection.close()


if __name__ == "__main__":
    main()
