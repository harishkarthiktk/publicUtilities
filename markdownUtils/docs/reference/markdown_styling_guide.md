# Markdown Specification for LLMs

Use this styling guide as a reference and follow as closely as possible.

## Indentation, Spacing and Punctuations
- Use a single tab character for indentation, not spaces.
- Place one blank line between sections and major elements.
- No trailing whitespace at end of lines.
- End files with a single newline character.
- Leave space between paragraphs, especially if the paragraphs are not related.
- End lines with a '.' if the line is terminating.
- End lines with ':' if there is indentation in the next line, to specify grouping.

---

## Headers
- Use ATX-style headers with `#` symbols.
- Add one space after the `#` symbol.
- Do not add empty line after `##` or other sub-headers.
- Use sentence case for headers.
- Hierarchy: `#` for title, `##` for sections, `###` for subsections.
- No periods at the end of headers.

---

## Lists
- Use `-` for unordered lists (not `*` or `+`).
- Use `1.` for ordered lists with period.
- Indent nested lists with one **tab** and not **space**.
- Add blank line before and after lists.
- No blank lines between list items unless they contain multiple paragraphs.

---

## Checkboxes
- Use `- [ ]` for unchecked items.
- Use `- [x]` for checked items.
- Add one space after the closing bracket.

---

## Code
- Use triple backticks for code blocks with language identifier: ```python```.
- Use single backticks for inline code: `variable`.
- Indent code block content consistently (use tabs if indenting manually).

---

## Emphasis
- Use as little emphasis as possible, and only if absolutely needed.
- Use `*italic*` for italic text (not `_`).
- Use `**bold**` for bold text.
- Use `***bold italic***` for combined emphasis.
- DO NOT USE any emojis.

---

## Links and Images
- Use `[text](url)` format for links.
- Use `![alt text](url)` format for images.
- Include descriptive alt text for all images.

---

## Tables
- Align headers and separators with pipes `|`.
- Use at least three hyphens `---` for separators.
- Add spaces around content: `| Cell |`.
- Left-align by default unless specified.

---

## Quotes
- Use `>` for blockquotes.
- Add space after `>`.
- Nest with additional `>` symbols: `>>`.

---

## Horizontal Rules
- Use `---` on its own line.
- Add blank lines before and after.
- Use horizontal after each `##` heading ends.

---

## Line Breaks
- Use two spaces at end of line for soft break (avoid when possible).
- Use blank line for paragraph breaks.
