# Raw Research Archive Verification

Repository: `Exploiter69/Prepped`
Branch: `main`

## Verification status (2026-10-19)

The user supplied a ZIP containing the five original research artifacts. The ZIP passed its integrity test and contains:

- Claude: Markdown source (56,775 bytes)
- Gemini Deep Research: Markdown source (51,345 bytes)
- DeepSeek: text source (57,062 bytes)
- Grok: PDF source (8 pages; image-only pages)
- Perplexity: PDF source (8 pages)

The existing Markdown files in `research/raw/` are **not verified exact copies** of those original artifacts. Comparison findings:

| Report | Existing archive file | Finding |
|---|---|---|
| Claude | `claude.md` | Source and archived Git blob SHA differ; not an exact match. |
| Gemini Deep Research | `gemini-deep-research.md` | Source is 51,345 bytes while the archived text is substantially shorter (37,738 characters); not an exact match. |
| DeepSeek | `deepseek.md` | Source and archived Git blob SHA differ; not an exact match. |
| Grok | `grok.md` | Original is an image-based PDF; OCR yields about 14,131 characters versus 16,651 characters in the Markdown archive. OCR is imperfect, so this is not a verbatim comparison. |
| Perplexity | `perplexity.md` | PDF text extraction yields about 57,940 characters versus 64,274 characters in the Markdown archive; not an exact match. |

## Important limitation

The uploaded originals have been inspected locally, but the original files have **not yet been committed into this repository**. The three text-source comparisons used the original files' bytes/Git blob hashes and the existing GitHub blob SHAs. The PDF comparisons are extraction/OCR-based and cannot establish byte-for-byte equality with Markdown.

Do not label any of the five existing Markdown files as an exact match. Preserve the uploaded originals unchanged and add them to the repository before replacing or regenerating archive content. For Grok and Perplexity, preserve the original PDFs themselves; any extracted Markdown should be clearly labeled as a derivative.

