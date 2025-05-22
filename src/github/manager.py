from src.tokens import TokenManager
import aiohttp
from typing import List
from github import Workflow, Github, ContentFile, Repository

class GithubManager:
    tokens: TokenManager
    def __init__(self, tokens: TokenManager):
        self.tokens = tokens
        self.headers = {
            "Authorization": f"Bearer {tokens.github_token}",
            "Accept": "application/vnd.github+json"
        }

        self.github = Github(tokens.github_token)

    async def trigger_workflow(self, user, repo, branch, workflow_file: str | Workflow.Workflow):
        if isinstance(workflow_file, Workflow.Workflow):
            workflow_file = str(workflow_file.id)

        url = f"https://api.github.com/repos/{user}/{repo}/actions/workflows/{workflow_file}/dispatches"
        json_data = { "ref": branch }  # branch to run on

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=json_data) as resp:
                return resp

    def get_active_repos(self, user, count = 3) -> List[Repository.Repository]:
        result = []

        user = self.github.get_user(user)
        repos = user.get_repos()
        for repo in repos:
            if repo.private:
                continue

            result.append(repo)

        result.sort(key=lambda x: x.updated_at, reverse=True)

        return result[:count]

    def get_active_branches(self, user, repo, count = 5):
        result = []

        user = self.github.get_user(user)
        repo = user.get_repo(repo)
        branches = repo.get_branches()

        result.extend(branches)
        result.sort(key=lambda x: x.commit.commit.timestamp, reverse=True)

        return result[:count]

    def get_triggerable_workflows(self, user, repo) -> List[Workflow.Workflow]:
        result = []

        # Get a repository
        repo = self.github.get_repo(f"{user}/{repo}")

        # List workflows
        workflows = repo.get_workflows()

        # Get workflow file content
        for workflow in workflows:
            if workflow.state != "active":
                continue

            content_file = repo.get_contents(workflow.path)
            if not isinstance(content_file, ContentFile.ContentFile):
                continue

            yaml_content = content_file.decoded_content.decode()

            # Check if the workflow is triggerable
            if "workflow_dispatch" in yaml_content:
                result.append(workflow)

        return result
