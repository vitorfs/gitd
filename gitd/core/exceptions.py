from django.core.exceptions import ValidationError


class GitHubException(ValidationError):
    pass
