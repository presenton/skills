# Presenton v3 API

Base URL: `https://api.presenton.ai`

## Access

Both endpoints in this reference are public. Send `Content-Type: application/json`; do not send an API key or authorization header.

## Search designs

`POST /api/v3/designs/search`

Request:

```json
{
  "query": "board-level quarterly review, editorial navy and cream, confident",
  "n": 4
}
```

Constraints:

- `query`: non-empty, at most 1000 whitespace-delimited words
- `n`: integer from 1 through 10

Response:

```json
[
  {
    "id": 7,
    "title": "Editorial Board Review",
    "description": "A restrained navy and cream system with large numerals..."
  }
]
```

Use one result's `title` and `description` as the visual brief for HTML generation. Preserve the selected result's `id` and include it as `design_id` in every export request for HTML based on that searched design. If the user supplied the design brief directly, do not search and omit `design_id`.

cURL:

```bash
curl --fail-with-body --silent --show-error \
  --request POST \
  --url https://api.presenton.ai/api/v3/designs/search \
  --header 'Content-Type: application/json' \
  --data '{"query":"board-level quarterly review, editorial navy and cream, confident","n":4}'
```

## Export HTML

`POST /api/v3/export/html-to-any`

Request:

```json
{
  "html": "<!doctype html><html>...</html>",
  "format": "pptx",
  "title": "Quarterly review",
  "design_id": 7
}
```

Fields:

- `html`: required non-empty string
- `format`: exactly one of `pptx`, `pdf`, or `png`
- `title`: optional string used for the exported presentation/file name
- `design_id`: optional integer ID of the selected result from design search; include it when a searched design was used

Response:

```json
{
  "url": "https://temporary-export-url.example/..."
}
```

Call the endpoint once for each requested format and never for an unrequested format. If a presentation was requested without a format, use `pptx` only. Return each response URL directly to the user as a clickable link. Do not download or save the exported file locally. The returned URL is presigned for 24 hours.

Format behavior:

- `pptx`: returns a `.pptx` file. DOM text and supported shapes remain editable where conversion permits.
- `pdf`: returns a 1280×720 px page per direct wrapper child.
- `png`: returns a URL for a ZIP containing one PNG per slide, not a single PNG file.

cURL:

```bash
curl --fail-with-body --silent --show-error \
  --request POST \
  --url https://api.presenton.ai/api/v3/export/html-to-any \
  --header 'Content-Type: application/json' \
  --data @request.json
```

If no searched design was used, omit `design_id` from the request.

## Errors

- `400`: empty/invalid HTML, missing `#presentation-slides-wrapper`, no direct slide children, or invalid format
- `404`: endpoint is not deployed at the selected API base URL
- `422`: invalid JSON schema, result count, or request field
- `502`: exporter unreachable, invalid exporter JSON, missing exporter URL, or upstream server failure

Error bodies normally use `detail`; some services may use `error`. Preserve the server message without exposing request secrets.
