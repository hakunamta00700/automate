"""GitHub Workflow Dispatch 명령어"""

import json

import click
import requests

from ...core.config import get_settings


@click.command()
@click.argument("url", type=str)
def dispatch(url: str) -> None:
    """GitHub workflow를 dispatch하여 비디오 전사를 실행합니다.

    Args:
        url: YouTube 비디오 URL
    """
    settings = get_settings()

    token = settings.GITHUB_TOKEN
    owner = settings.GITHUB_OWNER
    repo = settings.GITHUB_REPO

    if not all([token, owner, repo]):
        raise click.ClickException(
            "Missing required environment variables. Please check GITHUB_TOKEN, GITHUB_OWNER, and GITHUB_REPO in .env"
        )

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
    }
    data = {"event_type": "transcribe_from_url", "client_payload": {"url": url}}

    response = requests.post(
        f"https://api.github.com/repos/{owner}/{repo}/dispatches",
        headers=headers,
        data=json.dumps(data),
    )
    response.raise_for_status()
    click.echo(f"✅ GitHub workflow dispatched for URL: {url}")
