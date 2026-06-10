from pathlib import Path
from overtime import generate_overtime_report
from union_meal import generate_union_meal_report
from weekend_ot import generate_weekend_ot_report


def main() -> None:
    downloads = Path.home() / "Downloads"
    reporters = [
        ("Overtime report", generate_overtime_report),
        ("Union meal report", generate_union_meal_report),
        ("Weekend OT report", generate_weekend_ot_report),
    ]

    for description, reporter in reporters:
        try:
            output_path = reporter(output_dir=downloads)
            print(f"Saved {description} to {output_path}")
        except Exception as exc:
            print(f"{description} failed: {exc}")


if __name__ == "__main__":
    main()
