import os
import subprocess

# Find the project root (assume this script is in scripts/)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
APP_DIR = os.path.join(PROJECT_ROOT, "backend", "app")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "backend", "typeissues")

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)


def is_valid_folder(entry: str) -> bool:
    path = os.path.join(APP_DIR, entry)
    return os.path.isdir(path) and entry != "__pycache__"


def run_ruff_on_folder(folder: str) -> None:
    folder_path = os.path.join(APP_DIR, folder)
    output_path = os.path.join(OUTPUT_DIR, f"{folder}.md")
    with open(output_path, "w") as outfile:
        outfile.write(f"# Ruff Report for backend/app/{folder}\n")
        outfile.write(
            f"# CLI command for typechecking `ruff check backend/app/{folder}`\n\n"
        )
        try:
            result = subprocess.run(
                ["ruff", "check", "."],
                cwd=folder_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
            if result.stdout:
                outfile.write("```\n")
                outfile.write(result.stdout)
                outfile.write("```\n")
            else:
                outfile.write("No issues found.\n")
        except Exception as e:
            outfile.write(f"Error running ruff: {e}\n")


def main() -> None:
    for entry in os.listdir(APP_DIR):
        if is_valid_folder(entry):
            run_ruff_on_folder(entry)


if __name__ == "__main__":
    main()
