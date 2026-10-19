# Mesh-LLM evidence layer: two slides

Two 16:9 slides (1920x1080) on the Mesh-LLM evidence layer. Not deployed: the site's
Dockerfile does not copy `slides/`.

| File | What it is |
|---|---|
| `slide-1.html`, `slide-2.html` | Self-contained slides (inline CSS and SVG, no network). Add `?static` to skip the build-in. |
| `slide-1.png`, `slide-2.png` | The final frame of each slide at 1920x1080. |
| `mesh-llm-evidence.pptx` | Both slides as native, editable shapes and text (Arial), with speaker notes. Page size 20 x 11.25 in, so 1 pt = 1.333 px, as in the HTML. |
| `mesh-llm-evidence.pdf` | Both HTML slides printed to two pages. |
| `build_pptx.py` | Regenerates the pptx. All slide and notes text is in `TEXT` at the top. |
| `make_pdf.py` | Regenerates the pdf from the two HTML files (Playwright + Chromium, pypdf). |

Source for the claims: the capsules evidence plugin at v0.1.4
(<https://github.com/Mesh-LLM/capsules>), in particular `docs/TWIN-REFEREE-SELECTION.md` for the
second-node and referee row.
