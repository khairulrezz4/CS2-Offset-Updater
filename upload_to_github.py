"""
GitHub Upload Script - Uploads offset files to GitHub using GitHub CLI
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime

# Configuration
REPO_URL = "https://github.com/khairulrezz4/CS2-Offset-Updater"
REPO_DIR = Path(__file__).parent
OFFSETS_FILE = REPO_DIR / "offsets.json"
SCRIPT_FILE = REPO_DIR / "update_offsets_simple.py"

def run_command(cmd):
    """Run PowerShell command and return output"""
    try:
        result = subprocess.run(
            ["powershell", "-Command", cmd],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return 1, "", str(e)

def check_github_cli():
    """Check if GitHub CLI is installed"""
    code, output, error = run_command("gh --version")
    if code == 0:
        print(f"✓ GitHub CLI found: {output}")
        return True
    else:
        print("❌ GitHub CLI not found. Install from: https://cli.github.com/")
        return False

def init_git_repo():
    """Initialize git repo if not already initialized"""
    git_dir = REPO_DIR / ".git"
    if git_dir.exists():
        print("✓ Git repo already initialized")
        return True
    
    print("📦 Initializing git repository...")
    code, _, error = run_command(f"cd '{REPO_DIR}' ; git init")
    if code == 0:
        print("✓ Git repo initialized")
        return True
    else:
        print(f"❌ Failed to init git: {error}")
        return False

def add_remote():
    """Add GitHub remote"""
    code, output, error = run_command(f"cd '{REPO_DIR}' ; git remote -v")
    
    if "origin" not in output:
        print("🔗 Adding remote...")
        code, _, error = run_command(f"cd '{REPO_DIR}' ; git remote add origin '{REPO_URL}'")
        if code == 0:
            print("✓ Remote added")
            return True
        else:
            print(f"❌ Failed to add remote: {error}")
            return False
    else:
        print("✓ Remote already exists")
        return True

def configure_git():
    """Configure git user"""
    print("⚙️  Configuring git...")
    run_command(f"cd '{REPO_DIR}' ; git config user.email 'automated@offset-updater.local'")
    run_command(f"cd '{REPO_DIR}' ; git config user.name 'Offset Updater'")
    print("✓ Git configured")

def upload_files():
    """Stage, commit and push files"""
    print("📤 Uploading files to GitHub...")
    
    # Get current build from offsets.json
    try:
        with open(OFFSETS_FILE) as f:
            offsets = json.load(f)
        build_info = offsets.get('dwViewMatrix', 'unknown')
    except:
        build_info = 'auto-update'
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_msg = f"Update offsets - {timestamp} (dwViewMatrix: {build_info})"
    
    # Stage files
    print("  • Staging files...")
    run_command(f"cd '{REPO_DIR}' ; git add -A")
    
    # Check if there are changes
    code, output, _ = run_command(f"cd '{REPO_DIR}' ; git status --porcelain")
    if not output:
        print("✓ No changes to commit")
        return True
    
    # Commit
    print("  • Creating commit...")
    code, _, error = run_command(f"cd '{REPO_DIR}' ; git commit -m \"{commit_msg}\"")
    if code != 0:
        print(f"❌ Commit failed: {error}")
        return False
    print(f"✓ Committed: {commit_msg}")
    
    # Push using GitHub CLI
    print("  • Pushing to GitHub...")
    code, output, error = run_command(f"cd '{REPO_DIR}' ; git push -u origin main")
    
    if code == 0 or "are identical" in output:
        print("✓ Files pushed to GitHub")
        print(f"📍 Repository: {REPO_URL}")
        return True
    else:
        # Try master branch if main doesn't exist
        print("  • Trying master branch...")
        code, output, error = run_command(f"cd '{REPO_DIR}' ; git push -u origin master")
        if code == 0:
            print("✓ Files pushed to GitHub (master branch)")
            print(f"📍 Repository: {REPO_URL}")
            return True
        else:
            print(f"❌ Push failed: {error}")
            return False

def main():
    """Main upload workflow"""
    print("🚀 CS2 Offset Updater - GitHub Upload\n")
    
    if not check_github_cli():
        return False
    
    if not init_git_repo():
        return False
    
    if not add_remote():
        return False
    
    configure_git()
    
    if upload_files():
        print("\n✅ Upload complete!")
        return True
    else:
        print("\n❌ Upload failed")
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
