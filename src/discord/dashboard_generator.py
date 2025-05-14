import requests
from jinja2 import Template
import imgkit
from datetime import datetime, timedelta
import re
import os
from src.tokens import TokenManager

class DashboardGenerator:
    def __init__(self, tokens, repo, cache_dir):
        self.repo = repo
        self.cache_dir = cache_dir

        self.headers = {
            "Authorization": f"Bearer {tokens.github_token}",
            "Accept": "application/vnd.github+json"
        }

    #with open("dash.html") as f:
    #    template = Template(f.read())

    def get_latest_run_from_branch(self, branch):
        url = f"https://api.github.com/repos/{self.repo}/actions/runs"
        params = {"branch": branch, "per_page": 5}
        response = requests.get(url, headers=self.headers, params=params)
        runs = response.json().get("workflow_runs", [])
        if not runs:
            return None

        for run in runs:
            run = runs[0]
            run_id = run["id"]

            # Get jobs for this workflow run
            jobs_url = f"https://api.github.com/repos/{self.repo}/actions/runs/{run_id}/jobs"
            jobs_response = requests.get(jobs_url, headers=self.headers)
            job_data = jobs_response.json().get("jobs", [])

            grouped_jobs = {}
            print(job_data)
        """
        for job in job_data:
            name = job.get("name", "Unnamed Job")

            grouped_jobs.setdefault(group, {
                "icon": icon,
                "jobs": []
            })["jobs"].append({
                "name": name,
                "status": job.get("status"),
                "conclusion": job.get("conclusion"),
                "matrix": matrix,
                "started_at": job.get("started_at"),
                "completed_at": job.get("completed_at"),
            })

        return {
            "status": run.get("status", "unknown"),
            "conclusion": run.get("conclusion", "unknown"),
            "updated_at": run.get("updated_at", "N/A"),
            "html_url": run.get("html_url", "#"),
            "commit_sha": run.get("head_sha", ""),
            "groups": grouped_jobs
        }
        """

    def fetch_data(self):
        # Get list of branches
        branch_response = requests.get(
            f"https://api.github.com/repos/{self.repo}/branches",
            headers=self.headers
        )
        branch_list = branch_response.json()

        for branch in branch_list:
            self.get_latest_run_from_branch(branch["name"])

    def generate_image(self):
        data = self.fetch_data()
        """
        # Assemble the data for the dashboard
        data = []

        now = datetime.utcnow()
        cutoff = now - timedelta(days=7)

        for branch in branch_list:
            branch_name = branch["name"]
            run = get_latest_run_for_branch(branch_name)
            if run:
                run_time = datetime.strptime(run["updated_at"], "%Y-%m-%dT%H:%M:%SZ")
                if run_time >= cutoff:
                    data.append({
                        "name": branch_name,
                        "status": (
                            "success" if run["conclusion"] == "success" else
                            "failed" if run["conclusion"] == "failure" else
                            "running"
                        ),
                        "time": run["updated_at"],
                        "commit": run["commit_sha"][:7],
                        "time_dt": run_time  # Save datetime for sorting
                    })

        # Sort by latest run time descending
        data.sort(key=lambda x: x["time_dt"], reverse=True)

        # Drop the extra datetime field before rendering
        for d in data:
            del d["time_dt"]

        # Render
        html = template.render(branches=data)

        with open(self.cache_dir.joinpath("generated_dashbord.html"), "w") as f:
            f.write(html)

        imgkit.from_string(html, self.cache_dir.joinpath("dashboard.png"))

        """
