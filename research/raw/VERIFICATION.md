# Raw Research Archive Verification

Repository: `Exploiter69/Prepped`
Branch: `main`
Last verified: 2026-10-19

## Original source archive

The five supplied source files are preserved under `research/raw/originals/` in commit `fa3ea9b` (`Archive original AI research reports`). The three text originals' Git blob SHAs were checked against the uploaded ZIP's file bytes and match exactly. The two PDFs were copied unchanged and committed as binary files.

| Source | Archived path | Bytes | Git blob SHA |
|---|---|---:|---|
| Claude | `originals/claude.md` | 56,775 | `0f1eb4d0eb7acad2ca472a1f47a585071a66d19e` |
| Gemini Deep Research | `originals/gemini-deep-research.md` | 51,345 | `298923132019171f3f52b2c20755e0b5263e6dd7` |
| DeepSeek | `originals/deepseek.txt` | 57,062 | `8888fcd5432c7eab6ca99446c2af3187c7798fae` |
| Grok | `originals/grok_report.pdf` | 5,543,785 | `25c384d49410319cea074325442fcf52aa8ac5c9` |
| Perplexity | `originals/perplexity_report.pdf` | 1,226,022 | `55b6f9ef69f95cbeea5a61b37d72cd32cb333884` |

Paths in this table are relative to `research/raw/`.

## Comparison with the existing Markdown files

| Existing file | Existing Git blob SHA | Result |
|---|---|---|
| `claude.md` | `5b9d2bc529512c14bbe034029174067e354c56b9` | Differs from original Claude source; not an exact copy. |
| `gemini-deep-research.md` | `f80ea7bb9cb8b20bc962d6c8f7f30021cb0ce0a0` | Differs from original Gemini source; not an exact copy. |
| `deepseek.md` | `f0e0c0e17ff85168a5036551c2e11224ebe54aaf` | Differs from original DeepSeek source; not an exact copy. |
| `grok.md` | `312e3fa27ac4fa11f97705a5513cb45793013b8f` | Markdown derivative of a PDF; not byte-comparable and not verified as a verbatim transcription. |
| `perplexity.md` | `cd6f9c3bda56648feac901431acc77e469f76e72` | Markdown derivative of a PDF; not byte-comparable and not verified as a verbatim transcription. |

## Status and limitations

- The five original source files are now archived separately from the existing research files.
- Claude, Gemini, and DeepSeek originals have been checked by Git blob SHA against the uploaded source bytes; all three original archive files match exactly.
- The existing Claude, Gemini, and DeepSeek Markdown files do not match their original source files byte-for-byte. They have not been overwritten.
- Grok and Perplexity originals are PDFs, while their existing archive files are Markdown. A byte-for-byte comparison between those formats cannot establish textual fidelity. Treat the Markdown files as unverified derivatives until a careful extraction/OCR comparison is completed.
- Do not describe any existing Markdown derivative as an exact copy without further evidence.
