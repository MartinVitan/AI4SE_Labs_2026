import csv
from html import escape
import sys
import tempfile
from pathlib import Path

TASK_DIR = Path(__file__).resolve().parent
DATA_DIR = TASK_DIR / "data"
OUTPUT_PATH = TASK_DIR / "Task_2_results.svg"
sys.path.insert(0, str(DATA_DIR))

from evaluate_retrieval_predictions import evaluate_predictions


FRAMEWORK_OUTPUTS = (
    ("RACE", TASK_DIR / "RACEout.txt"),
    ("RTF", TASK_DIR / "RTFout.txt"),
    ("CO-STAR", TASK_DIR / "COSTARout.txt"),
)


def create_prediction_csv(source_path, destination_path):
    csv.field_size_limit(1_000_000_000)
    with source_path.open(encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames is None or "question" not in reader.fieldnames:
            raise ValueError()
        sql_column = next((column for column in ("predicted_sql", "sql") if column in reader.fieldnames), None,)
        if sql_column is None:
            raise ValueError()

        with destination_path.open("w", encoding="utf-8", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=("question", "predicted_sql"))
            writer.writeheader()
            for row in reader:
                writer.writerow({"question": row["question"],"predicted_sql": row[sql_column],})


def main():
    results = []
    with tempfile.TemporaryDirectory() as temporary_directory:
        for framework, source_path in FRAMEWORK_OUTPUTS:
            prediction_path = Path(temporary_directory) / f"{framework}.csv"
            create_prediction_csv(source_path, prediction_path)
            correct, total = evaluate_predictions(prediction_path)
            results.append((framework, correct / total))

    chart_left = 105
    chart_width = 650
    chart_top = 105
    chart_height = 220
    group_width = chart_width / len(results)
    bar_width = 90
    colors = ("#4f46e5", "#0891b2", "#16a34a")
    elements = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="860" height="430" '
        'viewBox="0 0 860 430" role="img" aria-labelledby="title">',
        "<title id=\"title\">Presná zhoda názvov (%)</title>",
        '<style>text{font-family:Segoe UI,Arial,sans-serif;fill:#1f2937}'
        ".muted{fill:#64748b}.grid{stroke:#dbe2ea;stroke-width:1}</style>",
        '<rect width="860" height="430" rx="14" fill="#f8fafc"/>',
        '<text x="38" y="48" font-size="24" font-weight="700">'
        "Presná zhoda názvov</text>",
        '<text x="28" y="215" font-size="13" text-anchor="middle" '
        'class="muted" transform="rotate(-90 28 215)">Úspešnosť (%)</text>',
    ]

    for tick in range(0, 101, 25):
        y = chart_top + chart_height * (1 - tick / 100)
        elements.append(f'<line x1="{chart_left}" y1="{y:g}" 'f'x2="{chart_left + chart_width}" y2="{y:g}" class="grid"/>')
        elements.append(f'<text x="{chart_left - 14}" y="{y + 4:g}" font-size="12" 'f'text-anchor="end" class="muted">{tick}%</text>')

    for index, ((framework, accuracy), color) in enumerate(zip(results, colors)):
        center_x = chart_left + group_width * (index + 0.5)
        bar_height = chart_height * accuracy
        bar_y = chart_top + chart_height - bar_height
        elements.extend(
            (
                f'<rect x="{center_x - bar_width / 2:g}" y="{bar_y:g}" '
                f'width="{bar_width}" height="{bar_height:g}" rx="5" '
                f'fill="{color}"/>',
                f'<text x="{center_x:g}" y="{bar_y - 10:g}" font-size="14" '
                f'text-anchor="middle" font-weight="700">{accuracy:.2%}</text>',
                f'<text x="{center_x:g}" y="{chart_top + chart_height + 28}" '
                f'font-size="14" text-anchor="middle" '
                f'font-weight="600">{escape(framework)}</text>',
            )
        )

    elements.append("</svg>")
    OUTPUT_PATH.write_text("\n".join(elements) + "\n", encoding="utf-8")
    for framework, accuracy in results:
        print(f"{framework}: {accuracy:.2%}")


if __name__ == "__main__":
    main()
