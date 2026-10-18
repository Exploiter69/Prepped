# Raw Research Archive Verification

Repository: `Exploiter69/Prepped`
Branch: `main`
Last verified: 2026-10-19

## Original source archive

The five supplied source files are preserved under `research/raw/originals/`. They were added in commit `fa3ea9b` (`Archive original AI research reports`). The three text originals' Git blob SHAs were checked against the uploaded ZIP's file bytes and match exactly. The two PDFs were copied unchanged and committed as binary files.

| Source | Archived path | Bytes | Git blob SHA |
|---|---|---:|---|
| Claude | `originals/claude.md` | 56,775 | `0f1eb4d0eb7acad2ca472a1f47a585071a66d19e` |
| Gemini Deep Research | `originals/gemini-deep-research.md` | 51,345 | `298923132019171f3f52b2c20755e0b5263e6dd7` |
| DeepSeek | `originals/deepseek.txt` | 57,062 | `8888fcd5432c7eab6ca99446c2af3187c7798fae` |
| Grok | `originals/grok_report.pdf` | 5,543,785 | `25c384d49410319cea074325442fcf52aa8ac5c9` |
| Perplexity | `originals/perplexity_report.pdf` | 1,226,022 | `55b6f9ef69f95cbeea5a61b37d72cd32cb333884` |

Paths in this table are relative to `research/raw/`.

## Text report corrections

The existing Markdown files for Claude, Gemini, and DeepSeek were replaced with the contents of their preserved originals. The root archive copies now have the same Git blob SHAs as the source originals:

| Existing path | Verified Git blob SHA | Status |
|---|---|---|
| `claude.md` | `0f1eb4d0eb7acad2ca472a1f47a585071a66d19e` | Exact byte-for-byte match to original source |
| `gemini-deep-research.md` | `298923132019171f3f52b2c20755e0b5263e6dd7` | Exact byte-for-byte match to original source |
| `deepseek.md` | `8888fcd5432c7eab6ca99446c2af3187c7798fae` | Exact byte-for-byte match to original source |

The original DeepSeek source is a `.txt` file; `deepseek.md` contains the same bytes, retained at the existing path for repository continuity.

## PDF-derived Markdown comparison

The original PDFs were extracted locally with `pdftotext` and, for Grok, rendered with `pdftoppm` and OCRed with Tesseract. A diagnostic comparison lowercased text, replaced URLs with a common placeholder, collapsed whitespace, and used Python `SequenceMatcher`. These scores assess only how the current Markdown compares with a machine-extracted PDF representation; they do **not** establish whether the archived Markdown matches the full AI response the user originally supplied. These are two separate verification questions.

| Source PDF | Existing Markdown | Extracted/normalized source | Normalized Markdown | Similarity | Assessment |
|---|---|---:|---:|---:|---|
| Grok OCR | `grok.md` | 14,015 characters | 16,526 characters | 85.2% | Partial textual similarity; OCR errors and content/format differences need review |
| Perplexity text extraction | `perplexity.md` | 39,275 characters | 44,875 characters | 84.8% | Partial textual similarity; content/format differences need review |

The raw Perplexity text extraction was 58,092 characters before normalization. Direct text extraction from Grok yielded only 8 bytes, so its 14,015-character comparison source came from OCR.

| Existing path | Git blob SHA | Repository provenance | PDF comparison status |
|---|---|---|---|
| `grok.md` | `312e3fa27ac4fa11f97705a5513cb45793013b8f` | Added in commit `d059ec9`, titled “Add original Grok competitor research report verbatim” | Not proven to be a verbatim transcription of the PDF; OCR comparison is inconclusive |
| `perplexity.md` | `cd6f9c3bda56648feac901431acc77e469f76e72` | Added in commit `f56e326`, titled “Archive original Perplexity research report” | Not proven to be a verbatim transcription of the PDF; text-extraction comparison is inconclusive |

A second comparison was performed after converting both PDFs to Markdown with PyMuPDF4LLM; the generated comparison files are committed under `research/raw/converted/`:

| PDF-derived comparison file | Characters | Existing Markdown | Characters |
|---|---:|---|---:|
| `converted/perplexity-from-pdf.md` | 45,677 | `perplexity.md` | 64,274 |
| `converted/grok-from-pdf.md` | 14,637 | `grok.md` | 16,651 |

The converted Perplexity file retains the main 18-section structure and contains the same key subsections checked (including core user journey, open-source/infrastructure projects, evaluation datasets, and acceptance criteria). Heading formatting and layout differ, and the converted file is shorter by 18,597 characters. That size difference alone does not establish that substantive content is missing; a detailed sentence/table-level review would be needed to certify completeness.

The Grok PDF required OCR (Tesseract, 300 DPI). Its conversion contains recognizable versions of all seven major report sections, but OCR artifacts remain and the Markdown's wording/length differs. OCR output cannot establish verbatim fidelity.

The converted files are comparison aids, not replacements for the originals or automatically authoritative transcriptions. No content in `grok.md` or `perplexity.md` was changed on the basis of conversion alone.

**Interpretation:** the repository history records `grok.md` as added verbatim and `perplexity.md` as an archived original report. The present PDF-conversion exercise has not disproved that provenance; it has only failed to establish exact equivalence between the Markdown and the PDF exports. The archived Markdown should not be labelled “unverified” without specifying which relationship is meant. A direct byte/text comparison against the original full AI responses, if preserved separately from the PDFs, would settle response-to-Markdown fidelity; PDF conversion alone cannot.
