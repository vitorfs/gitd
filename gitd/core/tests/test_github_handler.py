import uuid

from django.test import TestCase, override_settings

from gitd.core.constants import GitHubEvents
from gitd.core.exceptions import GitHubException
from gitd.core.handlers import github_handler
from gitd.core.models import Deployment


class TestGitHubHandler(TestCase):
    def test_ping(self):
        expected = "pong"
        actual = github_handler({}, GitHubEvents.PING, str(uuid.uuid4()))
        self.assertEqual(expected, actual)

    @override_settings(GITHUB_REPOSITORY="example/example")
    def test_deploy_bad_repo(self):
        data = {"repository": {"full_name": "example/bad-example"}}
        with self.assertRaisesMessage(GitHubException, "Invalid repository."):
            github_handler(data, GitHubEvents.PUSH, str(uuid.uuid4()))

    @override_settings(GITHUB_REPOSITORY="example/example", GITHUB_BRANCH="refs/heads/main")
    def test_deploy_bad_branch(self):
        data = {"ref": "refs/heads/dev", "repository": {"full_name": "example/example"}}
        expected = "Event ignored because it was not pushed to refs/heads/main."
        actual = github_handler(data, GitHubEvents.PUSH, str(uuid.uuid4()))
        self.assertEqual(expected, actual)

    @override_settings(
        GITHUB_REPOSITORY="example/example", GITHUB_BRANCH="refs/heads/main", GITD_DEPLOYMENT_COMMAND="echo 'deploy'"
    )
    def test_deploy_successful(self):
        data = {"ref": "refs/heads/main", "repository": {"full_name": "example/example"}}
        self.assertEqual(0, Deployment.objects.count())
        delivery_id = str(uuid.uuid4())
        actual = github_handler(data, GitHubEvents.PUSH, delivery_id)
        deployment = Deployment.objects.first()
        expected = "Deployment started with id %s." % deployment.pk
        self.assertEqual(expected, actual)
        self.assertIsNotNone(deployment)
        self.assertEqual(delivery_id, deployment.delivery)

    def test_bad_event(self):
        with self.assertRaisesMessage(GitHubException, "Invalid event."):
            github_handler({}, "BAD_EVENT", str(uuid.uuid4()))
