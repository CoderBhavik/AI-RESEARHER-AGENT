from pathlib import Path
import subprocess
import sys

ROOT_DIR = Path(__file__).resolve().parent


def main():
    subprocess.run(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "ui/app.py",
        ],
        cwd=ROOT_DIR,
    )


if __name__ == "__main__":
    main()