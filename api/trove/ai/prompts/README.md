# Prompts

Every prompt Trove sends to Claude lives here as a Markdown file, grouped by feature:
`prompts/<feature>/<name>.md`, loaded with `load_prompt("<feature>/<name>")`.

Rules:

- **One prompt per file.** No prompt text in Python strings longer than one line. A part several prompts
  share goes in its own file named `_part.md`, and a line `{{feature/_part}}` takes it in.
- **Stable text only.** Never put dates, IDs or member data in a prompt file. Per-request
  data goes in the `messages`, after the cached prefix, so prompt caching keeps working.
- **Every change runs the evals.** If you change a prompt, run `uv run python -m evals.run <feature>`
  (once that feature has evals) and say in the PR what changed in the output.
- **Grounding rule.** Anything that ends up in a member's book must trace back to the
  member's own words (docs/trove.md §4). Prompts must say so explicitly.
