# Prompt Engineering Log

Living document for the Doc Writer (Person 2) prompts. Update this **as you
iterate**, not at the end - every time `PROMPT_VERSION` in
`doc_writer/prompts.py` changes, add an entry here explaining why, with a
before/after example of the output.

This file is itself a hackathon deliverable, since the problem statement is
about generation quality, not just "an LLM was called."

---

## How to log a change

When you change a prompt:
1. Bump `PROMPT_VERSION` in `prompts.py` (e.g. `"v1"` -> `"v2"`). This
   automatically invalidates the cache for that prompt, so reruns regenerate
   fresh output instead of silently reusing stale cached docs.
2. Add a new `## vN` section below with:
   - **What changed** - the diff in plain English
   - **Why** - what problem you were seeing in the output
   - **Before** - a real generated output under the old prompt
   - **After** - the same endpoint's output under the new prompt

---

## v1 - initial generation & eval prompts

**What:** First version of `build_generation_prompt`, `build_eval_prompt`, and
`build_diff_summary_prompt`.

**Design decisions and why:**
- The generation system prompt explicitly says *"never invent parameters,
  fields, or behavior that isn't present in the input"* - early manual
  testing of raw LLM doc-generation (outside this pipeline) showed models
  readily hallucinate plausible-looking parameters or auth requirements that
  aren't actually in the source data. Grounding the prompt in "only use what
  you're given" is the main lever against that.
- Output is constrained to a fixed JSON shape (`description`, `parameters`,
  `request_example`, `response_example`, `edge_cases`) rather than free-form
  Markdown, so `generator.py` can parse it reliably and `output_writer.py`
  can render it consistently across every endpoint, regardless of language/
  framework the endpoint came from.
- The eval prompt runs at `temperature=0.0` (vs. `0.3` for generation) since
  we want the rubric score to be as reproducible as possible run-to-run -
  variance in creative wording is fine, variance in a *score* undermines
  citing it as a number.
- Eval system prompt explicitly says *"most first-draft docs score 3-4, not
  5"* to counter the LLM-as-judge tendency to rate everything highly by
  default; without this nudge, self-eval numbers tend to be inflated and not
  actually informative.

**Before / after:** not applicable yet - this is the first version. Once you
run this against real output from Person 1's extractor (or the bundled
`fixtures/sample_extracted.json`), paste a real example here and start the
`v2` section when you change anything.

**Open questions for later iteration:**
- Does `request_example`/`response_example` need real-looking sample *data*
  (fake names/ids), or is a schema-shaped placeholder good enough for the
  80% clarity bar? Decide once eval scores come back.
- Should `edge_cases` be capped at N items so verbose endpoints don't dwarf
  simple ones in the rendered doc?
