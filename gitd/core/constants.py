from django.utils.translation import gettext_lazy as _


class Services:
    GITHUB = "github"

    CHOICES = ((GITHUB, _("GitHub")),)


class GitHubEvents:
    PING = "ping"
    PUSH = "push"
