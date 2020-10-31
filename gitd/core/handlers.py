import subprocess
from gettext import gettext
from typing import Dict

from django.conf import settings

from gitd.core.constants import GitHubEvents, Services
from gitd.core.exceptions import GitHubException
from gitd.core.models import Deployment


class GitHubHandler:
    def ping(self) -> str:
        return "pong"

    def deploy(self, data: Dict, delivery_id: str) -> str:
        if data["repository"]["full_name"] != settings.GITHUB_REPOSITORY:
            raise GitHubException(message=gettext("Invalid repository."), code="GH02")
        if data["ref"] != settings.GITHUB_BRANCH:
            return gettext("Event ignored because it was not pushed to %s.") % settings.GITHUB_BRANCH

        subprocess.Popen(settings.GITD_DEPLOYMENT_COMMAND)
        deployment = Deployment.objects.create(service=Services.GITHUB, delivery=delivery_id)

        return gettext("Deployment started with id %s.") % deployment.id

    def __call__(self, data: Dict, event: str, delivery_id: str) -> str:
        if event == GitHubEvents.PING:
            return self.ping()
        elif event == GitHubEvents.PUSH:
            return self.deploy(data, delivery_id)
        else:
            raise GitHubException(message=gettext("Invalid event."), code="GH01")


github_handler = GitHubHandler()
