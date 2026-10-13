"""Publish site/ to the gh-pages branch (GitHub Pages), without a GitHub Actions workflow.

Builds site/startups.json, snapshots the site/ folder into a commit on gh-pages
(using a temporary git index, so main's working tree is untouched) and pushes it.
Usage: python scripts/publish_pages.py
GitHub Pages must be enabled once: Settings > Pages > Deploy from branch > gh-pages / root.
"""
import os
import subprocess
import tempfile

from common import ROOT

SITE = ROOT / "site"


def git(*args, env=None, input=None):
    return subprocess.run(["git", "-C", str(ROOT), *args], check=True, capture_output=True,
                          text=True, env=env, input=input).stdout.strip()


def main():
    subprocess.run(["python", str(ROOT / "scripts" / "build_site.py"), "--candidates"], check=True)
    (SITE / ".nojekyll").touch()

    with tempfile.TemporaryDirectory() as tmp:
        env = {**os.environ, "GIT_INDEX_FILE": os.path.join(tmp, "index")}
        git(f"--work-tree={SITE}", "add", "-A", "-f", ".", env=env)
        tree = git("write-tree", env=env)
    parent = []
    try:
        parent = ["-p", git("rev-parse", "--verify", "-q", "refs/remotes/origin/gh-pages")]
    except subprocess.CalledProcessError:
        pass
    src = git("rev-parse", "--short", "HEAD")
    commit = git("commit-tree", tree, *parent, input=f"Publish site from main@{src}\n")
    git("push", "origin", f"{commit}:refs/heads/gh-pages")
    git("fetch", "-q", "origin", "gh-pages")
    print(f"gh-pages <- {commit[:7]} (site from main@{src})")


if __name__ == "__main__":
    main()
