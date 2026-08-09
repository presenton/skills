# HTML format for html-to-any

## Temporary-file policy

Create working HTML only inside a private directory returned by `mktemp -d`, `tempfile.TemporaryDirectory()`, or the platform's equivalent OS temporary-directory facility. Never write generated HTML or exported PPTX, PDF, PNG, or ZIP files into the workspace, repository, home directory, or another persistent location. Submit the temporary HTML to the API and return the response URL without downloading it.

## Required document structure

Submit a complete HTML document. It must contain exactly one wrapper with the required ID, and every direct element child becomes one slide/page:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  </head>
  <body class="m-0 p-0">
    <main id="presentation-slides-wrapper" class="m-0 w-[1280px] p-0">
      <section class="relative h-[720px] w-[1280px] overflow-hidden" data-speaker-note="Optional note">...</section>
      <section class="relative h-[720px] w-[1280px] overflow-hidden">...</section>
    </main>
  </body>
</html>
```

Do not wrap slides in another container inside `#presentation-slides-wrapper`. A nested group counts as one slide because only direct children are exported.

## Dimensions and pagination

- Make every slide exactly 1280×720 px (16:9).
- Use `h-[720px] w-[1280px] overflow-hidden` on every slide and resolve overflow before export.
- Keep the wrapper at 1280 px wide and remove default document margins.
- Do not add margins or gaps between direct slide elements.
- Presenton injects print rules that page-break after each direct child for PDF and PNG generation.

## Tailwind styling

- Load Tailwind with `<script src="https://cdn.tailwindcss.com"></script>` in `<head>`.
- Express all visual styling with Tailwind utility classes, including arbitrary pixel values when required.
- Do not use inline `style` attributes or embedded `<style>` blocks.
- Keep the CDN script in the submitted HTML; the exporter waits for Tailwind to finish applying styles.

## Assets and fonts

- Use complete inline SVG only for non-chart artwork and icons.
- Use absolute HTTPS URLs or `data:` URLs for images and fonts. Local and relative filesystem paths are not reachable by the exporter.
- Include meaningful `alt` text on images.
- Use common fallback fonts. Web fonts may be used, but the exporter can only preserve what loads before stabilization and what the target format supports.
- Ensure every image has explicit dimensions and a deliberate `object-fit` value.

## Chart.js charts

- Use Chart.js for every data chart; do not hand-build charts with HTML, CSS, or SVG.
- Load it with `<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>` in `<head>` whenever a chart is present.
- Give every canvas a unique ID and fixed `width` and `height` attributes.
- Initialize each canvas directly with `document.querySelector("#chart-unique-id")` and one `new Chart(...)` call.
- Set `responsive: false` and `animation: false` so the exporter sees a stable chart.
- Use the selected design's palette, typography, grid, and labeling rules in Chart.js options.
- Do not use delayed timers, loops over canvas classes, or interaction-dependent rendering.

## PPTX compatibility

Presenton reads the rendered DOM and computed styles to create PPTX elements. For the most editable result:

- Keep text as HTML text elements rather than baking it into images.
- Prefer Tailwind solid fills, borders, simple gradients, flexbox, grid, positioned boxes, `<img>`, and simple SVG.
- Avoid CSS filters, backdrop filters, masks, unusual blend modes, video, and animation.
- Chart.js canvases may be captured as screenshots and may not remain editable in PPTX.
- Avoid content that depends on interaction, hover state, delayed timers, or user input.

## Speaker notes

When notes are requested, place exactly one `data-speaker-note` attribute on each slide element and escape quotes correctly. Do not add separate note elements elsewhere in the wrapper; the exporter collects every matching attribute in DOM order.

## Applying a searched design

Do not generate HTML until design search has returned results and one result has been selected. Translate that result's title and description into a small design system before writing slides:

- background and surface colors
- text and accent colors with accessible contrast
- title, body, and numeric type scale
- spacing unit and safe content bounds
- corner, border, and shadow language
- image treatment and chart palette

Apply that system consistently, but choose a content-appropriate layout per slide. Replace all sample styling from the bundled HTML asset. The search result is a mandatory visual brief; no design ID or special markup is sent to html-to-any.

## Preflight checklist

- Complete document with `<html>`, `<head>`, and `<body>`
- Tailwind CDN script present
- Exactly one `#presentation-slides-wrapper`
- At least one direct element child
- 1280×720 dimensions present and applied to every slide
- No overflow, clipping, accidental scrollbars, or off-canvas text
- No relative/local asset URLs
- No inline `style` attributes or embedded `<style>` blocks
- Chart.js CDN, unique fixed-size canvas IDs, and non-animated initialization present for every chart
- Same final HTML used for PPTX, PDF, and PNG exports
