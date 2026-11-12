"""Publish v2 shuffled review presentation without changing v1 packets or feedback."""

import json
from pathlib import Path
from typing import Any

from prepare import AUDIT, CALIBRATION, OUTPUT, write_once

from extraction_service.retrieval.core import canonical, digest


def shuffled_packets(output: Path) -> dict[str, Any]:
    """Shuffle by a declared deterministic salt; preserve all original item identities."""

    bundles = json.loads((output / "bundles.json").read_bytes())
    mapping = json.loads((output / "private-mapping.json").read_bytes())
    order: dict[str, list[str]] = {}
    for phase, cases in (("calibration", CALIBRATION), ("audit", AUDIT)):
        selected = [
            bundle
            for bundle in bundles
            if bundle["id"] in mapping and mapping[bundle["id"]]["key"].split("/")[0] in cases
        ]
        selected.sort(key=lambda bundle: digest(f"P03-S08-review-v2/{bundle['id']}".encode()))
        order[phase] = [bundle["id"] for bundle in selected]
        lines = [
            f"# S08 {phase} review — shuffled presentation v2",
            "",
            "Same items and IDs as v1; only presentation order changes.",
            "Earlier technique identities were exposed; this does not restore blinded review.",
            "Existing feedback is retained separately. No unreviewed verdict is a pass.",
            "Review correctness, completeness, citations and abstention separately.",
            "",
        ]
        for bundle in selected:
            lines.extend(
                [
                    f"## {bundle['id']}",
                    "",
                    "```json",
                    json.dumps(bundle, indent=2, ensure_ascii=False),
                    "```",
                    "",
                ]
            )
        write_once(output / f"{phase}-review-v2.md", "\n".join(lines).encode())
    result = {
        "version": "P03-S08-review-v2",
        "order": order,
        "bundles_sha256": digest(canonical(bundles)),
        "authority": "presentation only; no semantic labels changed",
    }
    write_once(output / "review-order-v2.json", json.dumps(result, indent=2).encode() + b"\n")
    return result


if __name__ == "__main__":
    print(json.dumps(shuffled_packets(OUTPUT), indent=2))
