# Presenton Skills

Agent skills for creating presentation files with [Presenton](https://presenton.ai).

The included `presenton` skill turns presentation requests into editable PPTX files, PDFs, and PNG slide images. It can search Presenton designs and icons, upload user-provided images, validate generated slide HTML, export each requested format, and return a shareable preview link.

## Get the skill

- [ClawHub](https://clawhub.ai/presenton/skills/presenton)
- [skills.sh](https://www.skills.sh/presenton/skills/presenton)

You can also copy [`skills/presenton`](skills/presenton) into the skills directory used by your compatible agent.

## What it supports

- PPTX, PDF, and PNG exports
- Custom design briefs or Presenton design search
- User-provided images and searchable icons
- Editable HTML text in generated PowerPoint files
- Shareable presentation previews
- HTML structure, asset, and font validation before export

The skill uses Presenton's public API at `https://api.presenton.ai`; no API key is required.

## Repository layout

```text
skills/presenton/
├── SKILL.md                  # Skill instructions and workflow
├── agents/openai.yaml        # Agent-facing metadata
├── references/               # API and HTML format documentation
├── scripts/                  # Export, asset, and validation helpers
└── tests/                    # Helper test suite
```

## Development

Run the test suite from the repository root:

```bash
python3 -m unittest discover -s skills/presenton/tests
```

Validate a presentation HTML file with:

```bash
python3 skills/presenton/scripts/validate_html.py /path/to/presentation.html
```

## License

Licensed under the [Apache License 2.0](LICENSE).
