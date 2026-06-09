"""Shared pure-Python Levenshtein edit distance.

Single canonical copy used by the cross-device synchronization gate
(``assembly.synth_input``) and the finding-stability metric
(``assembly.finding_stability``).

NOTE: the two consumers wrap this with OPPOSITE-semantics ``levenshtein_ratio``
functions — ``synth_input`` treats the ratio as a DRIFT score (0.0 = identical,
1.0 = disjoint) and ``finding_stability`` as a SIMILARITY score (1.0 = identical,
0.0 = disjoint). Only the distance primitive is shared; each module keeps its own
ratio wrapper so the two conventions cannot be accidentally swapped.
"""
from __future__ import annotations


def levenshtein_distance(a: str, b: str) -> int:
    """Classic Levenshtein edit distance. Pure-Python, no third-party dep.

    The minimum number of single-character insertions, deletions, or
    substitutions to transform ``a`` into ``b``. O(n*m) time, O(min(n, m))
    space (rolling row; iterate over the longer string, store the shorter).
    Adequate for prose paragraphs; callers run it well under the cost of an
    LLM dispatch.
    """
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    # Ensure b is the shorter to minimize memory.
    if len(a) < len(b):
        a, b = b, a
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        current = [i] + [0] * len(b)
        for j, cb in enumerate(b, start=1):
            insertions = previous[j] + 1
            deletions = current[j - 1] + 1
            substitutions = previous[j - 1] + (0 if ca == cb else 1)
            current[j] = min(insertions, deletions, substitutions)
        previous = current
    return previous[-1]
