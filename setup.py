#!/usr/bin/env python3
"""
One-time setup script for the Industrial Operations Brain Ingestion Service.
Verifies Tesseract is installed and checks all dependencies.
"""

import shutil
import subprocess
import sys
from pathlib import Path


def check_python():
    version = sys.version_info
    if version < (3, 9):
        print(f"✗ Python 3.9+ required, got {version.major}.{version.minor}")
        sys.exit(1)
    elif version < (3, 10):
        print(
            f"⚠  Python {version.major}.{version.minor}.{version.micro} (3.10+ recommended, but 3.9 works)"
        )
    else:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro}")


def check_tesseract():
    path = shutil.which("tesseract")
    if path:
        result = subprocess.run(
            ["tesseract", "--version"], capture_output=True, text=True
        )
        version_line = (
            result.stdout.split("\n")[0]
            if result.stdout
            else result.stderr.split("\n")[0]
        )
        print(f"✓ Tesseract found at {path} ({version_line.strip()})")
    else:
        print("✗ Tesseract NOT found on PATH")
        print("  Install: https://github.com/tesseract-ocr/tesseract")
        print("  macOS:   brew install tesseract")
        print("  Ubuntu:  sudo apt install tesseract-ocr")
        print("  (OCR features will be disabled until Tesseract is installed)")


def check_env():
    env_file = Path(".env")
    example_file = Path(".env.example")
    if not env_file.exists():
        if example_file.exists():
            import shutil

            shutil.copy(str(example_file), str(env_file))
            print("✓ Created .env from .env.example (fill in your API keys)")
        else:
            print("⚠  No .env file found. Create one from .env.example")
    else:
        print("✓ .env file found")


def check_disk_space():
    import shutil as sh

    usage = sh.disk_usage(Path.cwd())
    free_gb = usage.free / (1024**3)
    if free_gb < 1.0:
        print(f"⚠  Low disk space: {free_gb:.2f} GB free (recommend 1+ GB)")
    else:
        print(f"✓ Disk space: {free_gb:.1f} GB free")


def generate_demo_docs():
    """Pre-generate the demo corpus."""
    demo_script = Path("demo_docs/generate_demo_docs.py")
    if demo_script.exists():
        print("\nGenerating demo corpus...")
        try:
            subprocess.run([sys.executable, str(demo_script)], check=True)
        except subprocess.CalledProcessError as e:
            print(f"⚠  Demo doc generation failed: {e}")
    else:
        print("⚠  demo_docs/generate_demo_docs.py not found, skipping")


if __name__ == "__main__":
    print("=" * 50)
    print("Industrial Operations Brain — Setup Check")
    print("=" * 50)

    check_python()
    check_tesseract()
    check_env()
    check_disk_space()

    if "--no-demo" not in sys.argv:
        generate_demo_docs()

    print("\n" + "=" * 50)
    print("Setup complete! Start the service with:")
    print("  uvicorn ingestion.main:app --reload")
    print("=" * 50)
