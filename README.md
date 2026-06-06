# epub2typst

A very simple module that allows converting HTML elements from an epub into Typst markup.

For example:

```python
from epub2typst import Translator


t = Translator("myepub.epub")

# Individual chapters can be selected
t = t[4:10]

# Add conversion rules: add_rule(css selector, prefix, postfix)
# The body of the selected element will be output prepended with the prefix markup
# and appended with the postfix.
t.add_rule("h1", "= ", "")
t.add_rule("h2", "== ", "")
t.add_rule("blockquote", "#quote(block: true)[", "]")
t.add_rule("i", "_", "_")
t.add_rule("b", "*", "*")

# Triplicate newlines (or greater) will be collapsed to doublets
# and double spaces (or greater) will be collapsed into single spaces
t.add_rule("p", "\n\n", "\n\n")

# An optional function argument can be applied to the body of the element
t.add_rule("span[class=smallcaps]", "#smallcaps[", "]", lambda s: s.lower())

with open("text.typst", "w") as f:
    print(str(t), file=f)