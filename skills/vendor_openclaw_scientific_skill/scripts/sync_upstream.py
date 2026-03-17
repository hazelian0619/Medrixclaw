#!/usr/bin/env python3
"""
Sync OpenClaw Scientific Skill with upstream Claude Scientific Skills.

Usage:
    python sync_upstream.py --check          # Check for updates
    python sync_upstream.py --sync           # Sync changes
    python sync_upstream.py --auto           # Check and auto-sync if needed
"""

import argparse
import os
import json
import requests
from datetime import datetime

UPSTREAM_REPO = "K-Dense-AI/claude-scientific-skills"
UPSTREAM_BRANCH = "main"
SHA_FILE = ".upstream_sha"
SKILL_DIR = os.path.dirname(os.path.abspath(__file__))

def get_latest_commit():
    """Get latest commit SHA from upstream."""
    url = f"https://api.github.com/repos/{UPSTREAM_REPO}/commits/{UPSTREAM_BRANCH}"
    headers = {"Accept": "application/vnd.github.v3+json"}
    
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        raise Exception(f"Failed to fetch upstream: {resp.status_code}")
    
    data = resp.json()
    return {
        "sha": data["sha"],
        "message": data["commit"]["message"],
        "date": data["commit"]["author"]["date"],
        "url": data["html_url"]
    }

def get_last_synced():
    """Get last synced SHA."""
    sha_file = os.path.join(SKILL_DIR, SHA_FILE)
    if os.path.exists(sha_file):
        with open(sha_file, "r") as f:
            return f.read().strip()
    return None

def save_synced(sha):
    """Save synced SHA."""
    sha_file = os.path.join(SKILL_DIR, SHA_FILE)
    with open(sha_file, "w") as f:
        f.write(sha)

def get_changes_since(sha):
    """Get commits since given SHA."""
    url = f"https://api.github.com/repos/{UPSTREAM_REPO}/compare/{sha}...{UPSTREAM_BRANCH}"
    headers = {"Accept": "application/vnd.github.v3+json"}
    
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        return None
    
    data = resp.json()
    return {
        "ahead_by": data.get("ahead_by", 0),
        "commits": [
            {
                "sha": c["sha"][:7],
                "message": c["commit"]["message"],
                "date": c["commit"]["author"]["date"]
            }
            for c in data.get("commits", [])
        ]
    }

def check_updates():
    """Check for upstream updates."""
    print(f"🔍 Checking upstream: {UPSTREAM_REPO}")
    
    latest = get_latest_commit()
    last_synced = get_last_synced()
    
    print(f"\n📍 Latest upstream commit:")
    print(f"   SHA: {latest['sha'][:7]}")
    print(f"   Date: {latest['date']}")
    print(f"   Message: {latest['message'][:60]}...")
    
    if last_synced:
        print(f"\n📝 Last synced: {last_synced[:7]}")
        
        if latest['sha'] == last_synced:
            print("\n✅ Already up to date!")
            return False
        
        changes = get_changes_since(last_synced)
        if changes:
            print(f"\n🔄 {changes['ahead_by']} new commits:")
            for c in changes['commits'][:5]:
                print(f"   - {c['sha']}: {c['message'][:50]}...")
    else:
        print("\n⚠️  No previous sync found")
    
    return True

def sync_changes():
    """Sync changes from upstream."""
    print("🔄 Starting sync...")
    
    # This would spawn a subagent to do the actual sync
    # For now, just update the SHA
    
    latest = get_latest_commit()
    save_synced(latest['sha'])
    
    print(f"\n✅ Synced to {latest['sha'][:7]}")
    print("\nNext steps:")
    print("1. Review changes at:", f"https://github.com/{UPSTREAM_REPO}/commits/{UPSTREAM_BRANCH}")
    print("2. Update relevant files manually or via subagent")
    print("3. Commit and push changes")

def main():
    parser = argparse.ArgumentParser(description="Sync with upstream")
    parser.add_argument("--check", action="store_true", help="Check for updates")
    parser.add_argument("--sync", action="store_true", help="Sync changes")
    parser.add_argument("--auto", action="store_true", help="Auto sync if needed")
    args = parser.parse_args()
    
    if args.check:
        check_updates()
    elif args.sync:
        sync_changes()
    elif args.auto:
        if check_updates():
            sync_changes()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
