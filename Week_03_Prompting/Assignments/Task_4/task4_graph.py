import csv
import importlib.util
import sqlite3
from collections import Counter
from html import escape
from pathlib import Path

from scipy.stats import binomtest, wilcoxon


TASK_DIR = Path(__file__).resolve().parent
TASK2_DIR = TASK_DIR.parent / "Task_2"
TASK3_DIR = TASK_DIR.parent / "Task_3"
TASK3_EVALUATOR_PATH = TASK3_DIR / "f1.py"
OUTPUT_PATH = TASK_DIR / "Task_4_results.svg"

FRAMEWORKS = (
    ("RACE", TASK2_DIR / "RACEout.txt", 192),
    ("RTF", TASK2_DIR / "RTFout.txt", 152),
    ("CO-STAR", TASK2_DIR / "COSTARout.txt", 155),
)


def load_module(module_name, module_path):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError()

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def collect_question_scores(evaluator, predictions_path, connection):
    csv.field_size_limit(1_000_000_000)
    labels_by_question = evaluator.load_lbl(evaluator.LABELS_PATH)
    exact_results = []
    f1_results = []

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

        for line_number, row in enumerate(reader, start=2):
            question = row["question"]
            if question not in labels_by_question or not labels_by_question[question]:
                raise ValueError()

            expected_names = labels_by_question[question].pop(0)
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

            predicted_names = Counter()
            if name_column_index is not None:
                predicted_names = Counter(
                    result_row[name_column_index] for result_row in predicted_rows
                )

            exact_results.append(expected_names == predicted_names)
            f1_results.append(
                evaluator.calc_q_scores(expected_names, predicted_names)[2]
            )

    unmatched_labels = sum(
        len(results) for results in labels_by_question.values()
    )
    if unmatched_labels:
        raise ValueError()
    if len(exact_results) == 0:
        raise ValueError()

    return exact_results, f1_results


def collect_results():
    task3_evaluator = load_module("task3_evaluator", TASK3_EVALUATOR_PATH)
    database = task3_evaluator.load_db()
    results = []

    try:
        for framework, output_path, seconds in FRAMEWORKS:
            exact_results, f1_results = collect_question_scores(
                task3_evaluator, output_path, database
            )
            question_count = len(exact_results)
            results.append(
                {
                    "framework": framework,
                    "accuracy": sum(exact_results) / question_count * 100,
                    "f1": sum(f1_results) / question_count * 100,
                    "seconds": seconds,
                    "exact_per_question": exact_results,
                    "f1_per_question": f1_results,
                }
            )
    finally:
        database.close()

    return results


def holm_adjust(p_values):
    ordered = sorted(enumerate(p_values), key=lambda item: item[1])
    adjusted = [0.0] * len(p_values)
    largest_adjusted = 0.0

    for rank, (original_index, p_value) in enumerate(ordered):
        corrected = min(1.0, (len(p_values) - rank) * p_value)
        largest_adjusted = max(largest_adjusted, corrected)
        adjusted[original_index] = largest_adjusted

    return adjusted


def compare_frameworks(results):
    comparisons = []
    exact_p_values = []
    f1_p_values = []

    for first_index in range(len(results)):
        for second_index in range(first_index + 1, len(results)):
            first = results[first_index]
            second = results[second_index]
            first_exact = first["exact_per_question"]
            second_exact = second["exact_per_question"]

            first_only = sum(
                first_value and not second_value
                for first_value, second_value in zip(first_exact, second_exact)
            )
            second_only = sum(
                second_value and not first_value
                for first_value, second_value in zip(first_exact, second_exact)
            )
            discordant = first_only + second_only

            if discordant:
                exact_p_value = binomtest(
                    first_only, discordant, 0.5, alternative="two-sided"
                ).pvalue
            else:
                exact_p_value = 1.0

            f1_p_value = wilcoxon(
                first["f1_per_question"],
                second["f1_per_question"],
                alternative="two-sided",
            ).pvalue

            comparisons.append(
                {
                    "first": first["framework"],
                    "second": second["framework"],
                    "first_only": first_only,
                    "second_only": second_only,
                    "exact_p_raw": exact_p_value,
                    "f1_p_raw": f1_p_value,
                }
            )
            exact_p_values.append(exact_p_value)
            f1_p_values.append(f1_p_value)

    exact_adjusted = holm_adjust(exact_p_values)
    f1_adjusted = holm_adjust(f1_p_values)
    for index, comparison in enumerate(comparisons):
        comparison["exact_p_adjusted"] = exact_adjusted[index]
        comparison["f1_p_adjusted"] = f1_adjusted[index]

    return comparisons


def print_comparisons(comparisons):
    print("Frameworks       McNemar    Wilcoxon")

    for comparison in comparisons:
        exact_result = (
            "significant"
            if comparison["exact_p_adjusted"] < 0.05
            else "not"
        )
        f1_result = (
            "significant"
            if comparison["f1_p_adjusted"] < 0.05
            else "not"
        )
        framework_pair = comparison["first"] + " - " + comparison["second"]
        print(
            framework_pair.ljust(17)
            + exact_result
            + " (p = "
            + format(comparison["exact_p_adjusted"], ".3f")
            + ")    "
            + f1_result
            + " (p = "
            + format(comparison["f1_p_adjusted"], ".3f")
            + ")"
        )


def add_bar_chart(
    elements,
    results,
    top,
    height,
    maximum,
    tick_step,
    value_key,
    chart_title,
    value_suffix,
    colors,
):
    left = 110
    width = 700
    group_width = width / len(results)
    bar_width = 64
    elements.extend(
        (
            '<text x="60" y="' + str(top - 25) + '" font-size="19" '
            'font-weight="700">' + escape(chart_title) + "</text>",
            '<text x="28" y="' + str(top + height / 2) + '" font-size="13" '
            'text-anchor="middle" class="muted" transform="rotate(-90 28 '
            + str(top + height / 2)
            + ')">'
            + escape(value_suffix)
            + "</text>",
        )
    )

    for tick in range(0, maximum + 1, tick_step):
        y = top + height * (1 - tick / maximum)
        elements.extend(
            (
                '<line x1="' + str(left) + '" y1="' + format(y, ".1f")
                + '" x2="' + str(left + width) + '" y2="'
                + format(y, ".1f") + '" class="grid"/>',
                '<text x="' + str(left - 12) + '" y="'
                + format(y + 4, ".1f")
                + '" font-size="11" text-anchor="end" class="muted">'
                + str(tick) + value_suffix + "</text>",
            )
        )

    for index, result in enumerate(results):
        center = left + group_width * (index + 0.5)
        series = (
            (result["accuracy"], colors[0]),
            (result["f1"], colors[1]),
        ) if value_key == "percentage" else (
            (result["seconds"], colors[2]),
        )
        bar_gap = 8
        total_width = len(series) * bar_width + (len(series) - 1) * bar_gap

        for series_index, (value, color) in enumerate(series):
            bar_height = height * value / maximum
            x = center - total_width / 2 + series_index * (bar_width + bar_gap)
            y = top + height - bar_height
            label = format(value, ".2f") + value_suffix if value_key == "percentage" else str(value) + " s"
            elements.extend(
                (
                    '<rect x="' + format(x, ".1f") + '" y="'
                    + format(y, ".1f") + '" width="' + str(bar_width)
                    + '" height="' + format(bar_height, ".1f")
                    + '" rx="4" fill="' + color + '"/>',
                    '<text x="' + format(x + bar_width / 2, ".1f")
                    + '" y="' + format(y - 7, ".1f")
                    + '" font-size="11" text-anchor="middle" '
                    'font-weight="600">' + label + "</text>",
                )
            )

        elements.append(
            '<text x="' + format(center, ".1f") + '" y="'
            + str(top + height + 22)
            + '" font-size="13" text-anchor="middle" font-weight="600">'
            + escape(result["framework"]) + "</text>"
        )


def create_chart(results):
    elements = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="700" '
        'viewBox="0 0 900 700" role="img" aria-labelledby="title">',
        '<title id="title">Porovnanie prompting frameworkov</title>',
        '<style>text{font-family:Segoe UI,Arial,sans-serif;fill:#1f2937}'
        ".muted{fill:#64748b}.grid{stroke:#dbe2ea;stroke-width:1}</style>",
        '<rect width="900" height="700" rx="14" fill="#f8fafc"/>',
        '<text x="40" y="42" font-size="24" font-weight="700">'
        "Porovnanie prompting frameworkov</text>",
        '<rect x="535" y="58" width="14" height="14" rx="2" fill="#4f46e5"/>',
        '<text x="556" y="70" font-size="12">Presná zhoda (Task 2)</text>',
        '<rect x="710" y="58" width="14" height="14" rx="2" fill="#0891b2"/>',
        '<text x="731" y="70" font-size="12">Priemerné F1 (Task 3)</text>',
    ]

    add_bar_chart(
        elements,
        results,
        top=110,
        height=190,
        maximum=100,
        tick_step=20,
        value_key="percentage",
        chart_title="Úspešnosť podľa metrík",
        value_suffix="%",
        colors=("#4f46e5", "#0891b2", "#16a34a"),
    )

    add_bar_chart(
        elements,
        results,
        top=435,
        height=150,
        maximum=210,
        tick_step=30,
        value_key="time",
        chart_title="Čas generovania odpovede",
        value_suffix=" s",
        colors=("#4f46e5", "#0891b2", "#16a34a"),
    )

    elements.extend(
        (
            '<text x="60" y="640" font-size="12" class="muted">'
            "Časy v sekundách: RACE 3:12, RTF 2:32, CO-STAR 2:35. "
            "</text>",
            "</svg>",
        )
    )
    OUTPUT_PATH.write_text("\n".join(elements) + "\n", encoding="utf-8")


def main():
    results = collect_results()
    create_chart(results)
    comparisons = compare_frameworks(results)

    print_comparisons(comparisons)


if __name__ == "__main__":
    main()
