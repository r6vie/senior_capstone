"""The one place Trove talks to Claude.

Features never construct an Anthropic client. They take `claude: Claude = Depends(get_claude)`
in their router, pass it to their service functions, and load prompt text with
`load_prompt("<feature>/<name>")`. Tests swap in `tests.fakes.FakeClaude`.
"""
