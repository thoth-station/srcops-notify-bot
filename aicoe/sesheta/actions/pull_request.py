#!/usr/bin/env python3
# srcops-notify-bot
# Copyright(C) 2019,2020 Christoph Görn
#
# This program is free software: you can redistribute it and / or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


"""Sesheta's actions."""


import logging

from datetime import datetime
from typing import Optional
import gidgethub

from octomachinery.github.api.tokens import GitHubOAuthToken
from octomachinery.github.api.raw_client import RawGitHubAPI
from octomachinery.app.runtime.context import RUNTIME_CONTEXT

from aicoe.sesheta.actions.common import get_master_head_sha, get_pull_request, trigger_update_branch
from aicoe.sesheta.utils import eligible_release_pullrequest, get_release_issue


_LOGGER = logging.getLogger(__name__)


async def handle_release_pull_request(pullrequest: dict) -> tuple[str, str]:
    """Handle a Pull Request we created for a release."""
    github_api = RUNTIME_CONTEXT.app_installation_client

    if not eligible_release_pullrequest(pullrequest):
        _LOGGER.warning(f"Merged Release Pull Request: '{pullrequest['title']}', not eligible for release!")
        return

    commit_hash = pullrequest["merge_commit_sha"]
    release_issue = get_release_issue(pullrequest)
    release = pullrequest["head"]["ref"]

    # tag
    _LOGGER.info(f"Tagging release {release}: hash {commit_hash}.")

    tag = {"tag": str(release), "message": str(release), "object": str(commit_hash), "type": "commit"}
    response = await github_api.post(
        f"{pullrequest['base']['repo']['url']}/git/tags", preview_api_version="lydian", data=tag,
    )

    _LOGGER.debug("response: %s", response)

    tag_sha = response["sha"]

    tag_ref = {"ref": f"refs/tags/{release}", "sha": f"{tag_sha}"}
    await github_api.post(
        f"{pullrequest['base']['repo']['url']}/git/refs", data=tag_ref,
    )

    # comment on issue
    _LOGGER.info(f"Commenting on {release_issue} that we tagged {release} on hash {commit_hash}.")

    comment = {
        "body": f"I have tagged commit "
        f"[{commit_hash}]({pullrequest['base']['repo']['html_url']}/commit/{commit_hash}) "
        f"as release {release} :+1:",
    }
    await github_api.post(
        f"{pullrequest['base']['repo']['url']}/issues/{release_issue}/comments", data=comment,
    )

    # close issue
    _LOGGER.info(f"Closing {release_issue}.")

    await github_api.patch(
        f"{pullrequest['base']['repo']['url']}/issues/{release_issue}", data={"state": "closed"},
    )

    return commit_hash, release

    # happy! 💕


if __name__ == "__main__":
    pass
