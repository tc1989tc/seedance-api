#!/usr/bin/env python3
"""
Release script for seedance-sdk
"""
import subprocess
import sys
import re
from pathlib import Path


def get_current_version():
    """Get current version from pyproject.toml"""
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text()
    match = re.search(r'version = "([^"]+)"', content)
    return match.group(1) if match else None


def update_version(new_version):
    """Update version in pyproject.toml and __init__.py"""
    # Update pyproject.toml
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text()
    content = re.sub(
        r'version = "[^"]+"',
        f'version = "{new_version}"',
        content
    )
    pyproject_path.write_text(content)
    
    # Update __init__.py
    init_path = Path("seedance/__init__.py")
    content = init_path.read_text()
    content = re.sub(
        r'__version__ = "[^"]+"',
        f'__version__ = "{new_version}"',
        content
    )
    init_path.write_text(content)
    
    print(f"✅ Updated version to {new_version}")


def run_command(cmd):
    """Run shell command and handle errors"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Command failed: {cmd}")
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result.stdout.strip()


def main():
    """Main release process"""
    if len(sys.argv) != 2:
        print("Usage: python scripts/release.py <new_version>")
        print("Example: python scripts/release.py 1.0.1")
        sys.exit(1)
    
    new_version = sys.argv[1]
    
    # Validate version format
    if not re.match(r'^\d+\.\d+\.\d+$', new_version):
        print("❌ Version must be in format X.Y.Z")
        sys.exit(1)
    
    current_version = get_current_version()
    print(f"Current version: {current_version}")
    print(f"New version: {new_version}")
    
    # Confirm
    response = input(f"Release version {new_version}? (y/N): ")
    if response.lower() != 'y':
        print("❌ Release cancelled")
        sys.exit(0)
    
    # Update version
    update_version(new_version)
    
    # Run tests
    print("🧪 Running tests...")
    run_command("pytest tests/ -v")
    
    # Build package
    print("📦 Building package...")
    run_command("python -m build")
    
    # Check package
    print("🔍 Checking package...")
    run_command("twine check dist/*")
    
    # Git operations
    print("📝 Committing changes...")
    run_command(f"git add pyproject.toml seedance/__init__.py")
    run_command(f'git commit -m "Release version {new_version}"')
    run_command(f"git tag v{new_version}")
    
    print("🚀 Ready to push to GitHub!")
    print("Run the following commands to complete the release:")
    print(f"git push origin main")
    print(f"git push origin v{new_version}")
    print("\nThen create a GitHub release at:")
    print(f"https://github.com/tc1989tc/seedance-api/releases/new?tag=v{new_version}")


if __name__ == "__main__":
    main()
