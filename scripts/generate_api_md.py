import json
from pathlib import Path

spec_path = Path("docs/openapi.json")
if not spec_path.exists():
    raise SystemExit("docs/openapi.json not found")

with open(spec_path) as f:
    spec = json.load(f)

lines = [
    "# Vault API Reference (OpenAPI 3.1)",
    "",
    "Generated automatically from the FastAPI application schema.",
    "",
    f"**Title:** {spec.get('info', {}).get('title')}",
    f"**Version:** {spec.get('info', {}).get('version')}",
    f"**Description:** {spec.get('info', {}).get('description')}",
    "",
    "---",
    "",
]

paths = spec.get("paths", {})
for path, methods in sorted(paths.items()):
    lines.append(f"## `{path}`")
    lines.append("")
    for method, op in methods.items():
        summary = op.get("summary", "")
        desc = op.get("description", "")
        tags = ", ".join(op.get("tags", []))
        lines.append(f"### {method.upper()} `{path}`")
        if tags:
            lines.append(f"- **Tags:** {tags}")
        if summary:
            lines.append(f"- **Summary:** {summary}")
        if desc:
            lines.append(f"- **Description:** {desc}")

        params = op.get("parameters", [])
        if params:
            lines.append("")
            lines.append("**Parameters:**")
            for p in params:
                req = "required" if p.get("required") else "optional"
                lines.append(f"- `{p.get('name')}` ({p.get('in')}, {req}): {p.get('description', '')}")

        req_body = op.get("requestBody", {})
        if req_body:
            lines.append("")
            lines.append("**Request Body:**")
            content = req_body.get("content", {})
            for ctype, details in content.items():
                schema = details.get("schema", {})
                ref = schema.get("$ref") or schema.get("type") or ""
                lines.append(f"- Content-Type: `{ctype}` (Schema: `{ref}`)")

        responses = op.get("responses", {})
        if responses:
            lines.append("")
            lines.append("**Responses:**")
            for status, resp in responses.items():
                lines.append(f"- `{status}`: {resp.get('description', '')}")
        lines.append("")
    lines.append("---")
    lines.append("")

with open("docs/API.md", "w") as f:
    f.write("\n".join(lines))

print(f"Generated docs/API.md with {len(paths)} paths.")
