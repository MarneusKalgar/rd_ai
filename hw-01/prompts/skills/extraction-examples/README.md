# Synthetic extraction examples: development disclosure

This package illustrates existing frozen-v2 rules; it adds no new extraction
rule, automatic row filter or correction policy. SKILL.md and examples.json
are loaded in that order. This README is not loaded into model requests.

All names, codes, quantities and dates are invented. The topics were chosen
after observing catalog-row inclusion, generic-code ownership, package/quantity
confusion, copied order dates and unit errors in development gold10. These
examples are therefore benchmark-informed prompting, not an independent test
and not evidence of generalization. They contain no approved case output or
case identifiers. No original workbook or private mapping was consulted.

Each example contains one whole contract-valid expected object and a separate
explanation of the source roles. It must not supply rows to the actual PO.
Legitimate buyer codes, repeated ordered products and an explicitly selected
row with unavailable quantity provide contrasts to blanket nulling/filtering.
Examples are rendered identically for both adapters; only native Gemma inference
is included in the first experiment. Freeze the package before that run and
preserve any negative result rather than editing examples after observing it.
