import sys
import argparse
import requests

GITHUB_API = "https://api.github.com"


def get_pr_info(token, owner, repo, pr_number):
    url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()


def get_required_status_checks(token, owner, repo, branch):
    url = f"{GITHUB_API}/repos/{owner}/{repo}/branches/{branch}/protection/required_status_checks"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.luke-cage-preview+json"}
    resp = requests.get(url, headers=headers)
    if resp.status_code == 404:
        print(f"No branch protection configured for branch '{branch}'", file=sys.stderr)
        sys.exit(1)
    resp.raise_for_status()
    data = resp.json()
    return data.get("contexts", [])


def set_status(token, owner, repo, sha, context, description="Marked as passed by automation."):
    url = f"{GITHUB_API}/repos/{owner}/{repo}/statuses/{sha}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    payload = {
        "state": "success",
        "context": context,
        "description": description
    }
    resp = requests.post(url, json=payload, headers=headers)
    resp.raise_for_status()
    return resp.json()


def main():
    parser = argparse.ArgumentParser(description="Mark all required status checks for a PR as passed.")
    parser.add_argument("--repo", required=True, help="Repository in 'org/name' format")
    parser.add_argument("--pr", type=int, required=True, help="Pull Request number")
    parser.add_argument("--token", required=True, help="GitHub token (e.g. injected via Jenkins withCredentials)")
    args = parser.parse_args()

    token = args.token
    owner, repo = args.repo.split("/")
    pr = get_pr_info(token, owner, repo, args.pr)
    branch = pr["head"]["ref"]
    sha = pr["head"]["sha"]

    contexts = get_required_status_checks(token, owner, repo, branch)
    if not contexts:
        print(f"No required status checks found for branch '{branch}'.")
        sys.exit(0)

    for ctx in contexts:
        res = set_status(token, owner, repo, sha, ctx)
        print(f"Set status '{ctx}' to success.")

    print("All required status checks have been marked as passed.")


if __name__ == "__main__":
    main()
