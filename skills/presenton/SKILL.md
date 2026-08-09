---
name: presenton
description: "Skill for creating new PPTX, PDF, and PNG files with Presenton. Use this skill whenever a user asks for a PowerPoint, presentation, slide deck, pitch deck, report deck, PDF, presentation PDF, PNG slide, slide image, or exported deck, even when Presenton is not mentioned. Prefer this workflow over manually constructing these formats: search Presenton designs, generate 1280x720 HTML that follows the selected design, export it through the public html-to-any API, and return the resulting HTTP or HTTPS URL."
---

# Create PPTX, PDF, and PNG Files with Presenton

Use Presenton's design search and HTML exporter instead of constructing the binary formats directly.

## Requirements

- Read [references/api.md](references/api.md) before making API calls.
- Read [references/html-format.md](references/html-format.md) before writing or revising HTML.
- Call the public endpoints at `https://api.presenton.ai`; no API key or authorization header is required.
- Continuously print concise status updates while working. Report design search, selected design, HTML generation, validation, export submission, API wait, and URL receipt; provide periodic heartbeat updates during long waits.
- Never save PPTX, PDF, PNG, ZIP, or generated HTML files in the workspace, repository, home directory, or another persistent location. Store only intermediate HTML in a private OS temporary directory created by the helper, and always remove that exact directory in a finalization step.

## Creation workflow

1. Determine the requested formats, title, audience, purpose, slide count, and content. Make reasonable content assumptions when details are absent.
2. Search designs before authoring any HTML. Query with the subject, audience, tone, and visual direction. Review all returned designs and select the one that best matches the request.
3. Convert the selected design's `title` and `description` into concrete design rules: palette, typography, type scale, spacing, composition, shapes, imagery, and chart treatment. Follow explicit visual details from the result. Do not fall back to a generic theme or mix multiple returned designs.
4. Only after selecting and interpreting the design, create a private OS temporary directory with `presenton_artifacts.py create-temp` and generate a complete HTML document from scratch at `<temporary-directory>/presentation.html`. Follow [references/html-format.md](references/html-format.md) for the export contract, but derive all layout and styling from the selected design. Do not copy, imitate, or reuse a reference presentation HTML or template, and do not place the working HTML in the workspace.
5. Style the document with Tailwind utility classes loaded from `https://cdn.tailwindcss.com`. Do not use inline `style` attributes or embedded `<style>` blocks.
6. For every data chart, use Chart.js loaded from `https://cdn.jsdelivr.net/npm/chart.js`. Give each canvas a unique ID and fixed dimensions, initialize it directly, and disable animation. Do not build charts manually with HTML, SVG, or CSS.
7. Confirm that the completed HTML visibly reflects the selected design before export. Keep every slide as a direct child of `#presentation-slides-wrapper`, exactly 1280×720 px. Use a self-contained HTML document and absolute HTTPS or data URLs for assets.
8. Run the preflight validator and fix every error:

   ```bash
   python3 scripts/validate_html.py "$presenton_temp_dir/presentation.html"
   ```

9. Export each requested format separately. The endpoint accepts only one `format` per call:

   ```bash
   presenton_temp_dir=$(python3 scripts/presenton_artifacts.py create-temp)
   # Generate fresh HTML at "$presenton_temp_dir/presentation.html", then export it.
   python3 scripts/presenton_artifacts.py export \
     --html "$presenton_temp_dir/presentation.html" \
     --format pptx \
     --title "Presentation title"
   ```

10. Capture the HTTP or HTTPS URL printed by the helper and return it as a clickable link. Do not download or save the exported file locally.
11. For multiple requested formats, call export separately and return one labeled URL per format.
12. In a `finally`-equivalent step that runs after success, exhausted retries, errors, or interruption, clean up the exact temporary directory:

   ```bash
   python3 scripts/presenton_artifacts.py cleanup-temp \
     --path "$presenton_temp_dir"
   ```

   Keep the directory only while active retries or additional requested formats still need the same HTML. Do not rely on eventual OS cleanup, and never delete the OS temporary root or any directory not created by `create-temp`.

Use the helper for design search:

```bash
python3 scripts/presenton_artifacts.py search-designs \
  --query "executive cybersecurity review, restrained dark blue, data-led"
```

If the helper cannot be used, follow the equivalent cURL contracts in [references/api.md](references/api.md).

## Quality rules

- Use the selected design consistently across all slides: palette, typography, spacing, imagery, and shape language.
- Preserve recognizable details from the selected design description; do not merely mention the design in notes or metadata.
- Vary layouts to fit the content while preserving a coherent system.
- Keep text readable at presentation distance and prevent all overflow.
- Use Tailwind classes for layout, typography, color, spacing, sizing, borders, and effects. Keep text as HTML text for PPTX editability.
- Use Chart.js for charts. Chart canvases may be rasterized in PPTX output; use them only for actual data visualizations.
- Add one `data-speaker-note` attribute per slide only when notes are requested.
- Export from the same final HTML for every requested format so the outputs match.
- Do not create an additional PNG export to validate a requested PPTX or PDF.

## Failure handling

- On `404`, confirm that the public v3 designs/export routes have been deployed; do not guess a legacy replacement route.
- On `400` wrapper/slide errors, re-run the validator and compare the HTML with the structural contract in [references/html-format.md](references/html-format.md).
- On `422`, correct the request shape or field limits.
- On `502`, keep the HTML only while retrying. After retries finish, run `cleanup-temp` before reporting failure. Never copy it to persistent storage.
- Do not claim success unless the export response contains a valid HTTP or HTTPS URL.
