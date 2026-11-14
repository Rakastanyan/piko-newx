import os
import shutil
import subprocess
import sys

import requests


def github_api_headers() -> dict[str, str]:
    """Return authenticated headers for GitHub API requests when available."""
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def panic(message: str):
    print(message, file=sys.stderr)
    exit(1)


def download(link, out, headers=None):
    dir_name = os.path.dirname(out)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    if os.path.exists(out):
        print(f"{out} already exists skipping download")
        return

    # https://www.slingacademy.com/article/python-requests-module-how-to-download-files-from-urls/#Streaming_Large
    with requests.get(link, stream=True, headers=headers, timeout=30) as r:
        r.raise_for_status()
        with open(out, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)


def run_command(command: list[str]):
    cmd = subprocess.run(command, capture_output=True, shell=True)

    try:
        cmd.check_returncode()
    except subprocess.CalledProcessError:
        print(cmd.stdout)
        print(cmd.stderr)
        exit(1)


def sign_artifact(path: str) -> str | None:
    """Create a detached, ASCII-armored GPG signature for a release artifact.

    Mirrors how Morphe/Piko ship a `<bundle>.mpp.asc` next to the patch bundle.
    Returns the `.asc` path, or `None` when signing is unavailable (no gpg,
    no key, or signing fails). Signing failures are non-fatal so the unsigned
    bundle still ships.
    """
    asc_path = f"{path}.asc"
    if not shutil.which("gpg"):
        print("gpg not found; skipping detached signature")
        return None

    gpg_passphrase = os.environ.get("GPG_PASSPHRASE")
    sign_command = ["gpg", "--batch", "--yes", "--detach-sign", "--armor"]
    if gpg_passphrase:
        sign_command.extend(
            ["--pinentry-mode", "loopback", "--passphrase", gpg_passphrase]
        )
    sign_command.append(path)

    try:
        subprocess.run(
            sign_command,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        print(f"gpg detached signature failed: {exc.stderr}")
        return None

    return asc_path


def publish_release(tag: str, files: list[str], body: str, title: str):
    command = [
        "gh",
        "release",
        "create",
        tag,
        "--title",
        title,
        "--notes",
        body,
    ]

    for file in files:
        command.append(file)

    subprocess.run(command, env=os.environ.copy()).check_returncode()
