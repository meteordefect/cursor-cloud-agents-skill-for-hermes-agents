import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


API_BASE_URL = "https://api.cursor.com/v0"


class SkillError(Exception):
    pass


def _api_key():
    key = os.environ.get("CURSOR_API_KEY")
    if not key:
        raise SkillError("CURSOR_API_KEY is required")
    return key


def _request(method, path, body=None, query=None):
    url = f"{API_BASE_URL}{path}"
    if query:
        clean_query = {k: v for k, v in query.items() if v is not None}
        if clean_query:
            url = f"{url}?{urllib.parse.urlencode(clean_query)}"

    data = None
    headers = {
        "Authorization": "Basic "
        + base64.b64encode(f"{_api_key()}:".encode("utf-8")).decode("ascii")
    }

    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")

    request = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise SkillError(f"Cursor API error {exc.code}: {raw}") from exc
    except urllib.error.URLError as exc:
        raise SkillError(f"Cursor API request failed: {exc.reason}") from exc


def _require(payload, key):
    value = payload.get(key)
    if value is None or value == "":
        raise SkillError(f"{key} is required")
    return value


def _target(payload):
    target = {}
    mappings = {
        "auto_create_pr": "autoCreatePr",
        "open_as_cursor_github_app": "openAsCursorGithubApp",
        "skip_reviewer_request": "skipReviewerRequest",
        "branch_name": "branchName",
        "auto_branch": "autoBranch",
    }
    for source_key, cursor_key in mappings.items():
        if source_key in payload:
            target[cursor_key] = payload[source_key]
    return target or None


def _launch_agent(payload):
    source = {}
    if payload.get("pr_url"):
        source["prUrl"] = payload["pr_url"]
    else:
        source["repository"] = _require(payload, "repository")
        if payload.get("ref"):
            source["ref"] = payload["ref"]

    body = {
        "prompt": {"text": _require(payload, "prompt")},
        "source": source,
    }

    if payload.get("model"):
        body["model"] = payload["model"]

    target = _target(payload)
    if target:
        body["target"] = target

    return _request("POST", "/agents", body=body)


def _followup(payload):
    body = {"prompt": {"text": _require(payload, "prompt")}}
    agent_id = urllib.parse.quote(_require(payload, "agent_id"), safe="")
    return _request("POST", f"/agents/{agent_id}/followup", body=body)


def handle(payload):
    action = _require(payload, "action")

    if action == "me":
        return _request("GET", "/me")
    if action == "models":
        return _request("GET", "/models")
    if action == "repositories":
        return _request("GET", "/repositories")
    if action == "list_agents":
        return _request(
            "GET",
            "/agents",
            query={
                "limit": payload.get("limit"),
                "cursor": payload.get("cursor"),
                "prUrl": payload.get("pr_url"),
            },
        )
    if action == "launch_agent":
        return _launch_agent(payload)

    agent_id = urllib.parse.quote(_require(payload, "agent_id"), safe="")

    if action == "get_agent":
        return _request("GET", f"/agents/{agent_id}")
    if action == "followup":
        return _followup(payload)
    if action == "stop_agent":
        return _request("POST", f"/agents/{agent_id}/stop")
    if action == "conversation":
        return _request("GET", f"/agents/{agent_id}/conversation")
    if action == "list_artifacts":
        return _request("GET", f"/agents/{agent_id}/artifacts")
    if action == "download_artifact":
        return _request(
            "GET",
            f"/agents/{agent_id}/artifacts/download",
            query={"path": _require(payload, "artifact_path")},
        )

    raise SkillError(f"Unsupported action: {action}")


def main():
    payload = json.load(sys.stdin)
    try:
        result = {"ok": True, "data": handle(payload)}
    except SkillError as exc:
        result = {"ok": False, "error": str(exc)}
    json.dump(result, sys.stdout)


if __name__ == "__main__":
    main()
