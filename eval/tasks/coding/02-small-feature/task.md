---
id: coding-02-small-feature
type: small-feature
weight: 1.0
---
## Task Prompt

Add `merge_layers(layers)` to the `kvconfig` package and export it from `kvconfig`. It accepts an iterable of mappings. Normalize every key with the package’s existing key rules. Later layers override earlier ones; a value of `None` removes that normalized key if present. Return a new dictionary and do not mutate inputs. Raise `TypeError` when a layer is not a mapping or a key is not a string. Add focused tests in `tests/test_merge_layers.py`. Follow the package’s existing style and use only the standard library.
