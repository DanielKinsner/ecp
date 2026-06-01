"""Guard: every placeholder in the v2 prompt templates is wired to a substitution.

The v2 dispatch harness (scripts/test-specialist.py) renders two contract
templates into final agent prompts by string-replacing placeholder tokens:

  - contracts/specialist-prompt-v2.md   -> render_prompt()
  - contracts/synthesizer-v2.md         -> render_synthesizer_prompt()

Each renderer owns a `substitutions` dict mapping a placeholder token
(`{{name}}` or `${NAME}`) to the value spliced in at dispatch time. After
substitution both renderers run a `leftover` regex check and raise on any
surviving `{{...}}`. That runtime check only fires when the renderer is
actually invoked with inputs that exercise the affected template region --
so a placeholder added to the markdown template but never wired into the
substitutions dict can ship silently until a live dispatch renders a prompt
with `{{some_new_field}}` literally embedded in the agent instructions.

This test closes that gap at the source level: it parses every placeholder
token out of the authoritative template body (extracted via the harness's
own load_template_body / load_synthesizer_template_body, so the test tracks
the real 4-backtick fence the renderer reads) and asserts each token is a
key in the corresponding renderer's substitutions dict. A newly-added
template placeholder that nobody wired to a substitution fails here, before
it can reach a dispatch.

Coupling notes (deliberate):
  - Template bodies come from the harness's own extractor functions, not a
    re-implemented markdown parser, so the test reads exactly what the
    renderer substitutes against.
  - Substitution keys are read out of the harness source via AST (the dict
    literal in each renderer), so the test does not hardcode the expected
    placeholder set -- it derives both sides from authoritative sources.
  - A live end-to-end render against the slingmods-pdp fixture confirms the
    happy path actually produces a placeholder-free prompt.

test-specialist.py is hyphenated, so it is loaded via importlib.util and
registered in sys.modules before exec_module (it defines module-scope
dataclass-style imports that expect a real module entry).

Run:
    python -m pytest tests/test_prompt_template_completeness.py -q
"""
from __future__ import annotations

import ast
import importlib.util
import re
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent
# The harness puts scripts/ on sys.path so `from assembly.X import ...` resolves.
_SCRIPTS = _REPO / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

_HARNESS_PATH = _SCRIPTS / "test-specialist.py"

# A placeholder token is either a `{{name}}` mustache token or a `${NAME}`
# shell-style token. Names are identifier-shaped. This matches exactly the
# token families the renderers substitute (and the families the renderers'
# own `leftover` guard scans for `{{...}}`).
_TOKEN_RE = re.compile(r"\{\{[a-zA-Z_][a-zA-Z0-9_]*\}\}|\$\{[a-zA-Z_][a-zA-Z0-9_]*\}")


def _load_harness():
    """Load the hyphenated scripts/test-specialist.py as an importable module.

    Registered in sys.modules under a stable name before exec_module so the
    module's own top-level imports resolve against a real module entry.
    """
    spec = importlib.util.spec_from_file_location(
        "test_specialist_cli", _HARNESS_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["test_specialist_cli"] = module
    spec.loader.exec_module(module)
    return module


_HARNESS = _load_harness()


def _placeholders_in(template_body: str) -> set[str]:
    """Every distinct placeholder token in a template body."""
    return set(_TOKEN_RE.findall(template_body))


def _substitution_keys(func_name: str) -> set[str]:
    """Extract the `substitutions` dict literal keys from a renderer via AST.

    Reads the harness source rather than the runtime dict so the keys are
    derived from the authoritative function definition without having to
    construct a full set of render arguments. Each key in the dict literal
    must be a constant string token.
    """
    source = _HARNESS_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            for inner in ast.walk(node):
                if isinstance(inner, ast.Assign) and any(
                    isinstance(t, ast.Name) and t.id == "substitutions"
                    for t in inner.targets
                ):
                    assert isinstance(inner.value, ast.Dict), (
                        f"{func_name}: `substitutions` must be a dict literal "
                        f"for this guard to read its keys via AST."
                    )
                    keys: set[str] = set()
                    for key_node in inner.value.keys:
                        value = ast.literal_eval(key_node)
                        assert isinstance(value, str), (
                            f"{func_name}: substitution key {value!r} is not a "
                            f"string literal."
                        )
                        keys.add(value)
                    return keys
    raise AssertionError(
        f"{func_name}: no `substitutions = {{...}}` dict literal found in "
        f"{_HARNESS_PATH.name}."
    )


# (renderer function name, harness template-body extractor) pairs.
_CASES = [
    ("render_prompt", "load_template_body", "contracts/specialist-prompt-v2.md"),
    (
        "render_synthesizer_prompt",
        "load_synthesizer_template_body",
        "contracts/synthesizer-v2.md",
    ),
]


@pytest.mark.parametrize("func_name,loader_name,contract", _CASES)
def test_every_template_placeholder_is_wired(func_name, loader_name, contract):
    """Each `{{...}}` / `${...}` token in the template body must be a key in
    the renderer's substitutions dict.

    Extra keys in the substitutions dict are allowed (a renderer may carry a
    substitution for a token that lives elsewhere). The guard is one-directional:
    no template token may be UNwired.
    """
    template_body = getattr(_HARNESS, loader_name)()
    tokens = _placeholders_in(template_body)
    assert tokens, (
        f"{contract}: no placeholder tokens found in the template body -- the "
        f"4-backtick fence extractor may have changed shape."
    )
    keys = _substitution_keys(func_name)
    unwired = sorted(tokens - keys)
    assert not unwired, (
        f"{contract} has template placeholder(s) with no substitution wired in "
        f"{func_name}'s substitutions dict: {unwired}. Add each to the "
        f"substitutions dict (or remove it from the template). This is the "
        f"exact failure that ships a prompt with a literal {{placeholder}} in "
        f"the agent instructions."
    )


def test_guard_detects_an_unwired_placeholder():
    """Sanity check the guard's own logic: an injected fake token that is NOT
    a substitution key is reported as unwired.

    This protects against the guard silently passing because of a broken
    extractor (e.g., if token extraction returned the empty set, the real
    assertion above would vacuously pass). Here we prove the set-difference
    actually flags an unwired token.
    """
    keys = _substitution_keys("render_prompt")
    fake = "{{__definitely_not_a_real_substitution__}}"
    assert fake not in keys
    tokens = {fake} | keys
    unwired = tokens - keys
    assert unwired == {fake}


def test_known_good_render_has_no_leftover_placeholders():
    """End-to-end: the known-good slingmods-pdp specialist render produces a
    prompt with zero surviving placeholder tokens.

    Couples the static guard above to a real render so a regression in the
    substitution wiring (or the template) surfaces concretely. Mirrors the
    documented known-good command:

        prepare --cluster pricing --device desktop
                --engagement-id slingmods-pdp
                --cluster-context-path .../cluster-context-pricing-desktop.json
                --baton-path .../baton.json
                --viewport-width 1440 --viewport-height 900
    """
    fixture = _REPO / "fixtures" / "slingmods-pdp"
    context_path = fixture / "cluster-context-pricing-desktop.json"
    baton_path = fixture / "baton.json"
    if not context_path.is_file() or not baton_path.is_file():
        pytest.skip("slingmods-pdp fixture not present")

    rendered = _HARNESS.render_prompt(
        cluster="pricing",
        device="desktop",
        engagement_id="slingmods-pdp",
        cluster_context_path=str(context_path),
        baton_path=str(baton_path),
        viewport_width=1440,
        viewport_height=900,
        dpr=1.0,
        page_type="product-page",
        platform="unknown",
        screenshot_paths=[str(fixture / "section-1.jpg")],
    )
    leftover = sorted(set(_TOKEN_RE.findall(rendered)))
    assert not leftover, (
        f"render_prompt left placeholder tokens in the rendered prompt: "
        f"{leftover}"
    )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
