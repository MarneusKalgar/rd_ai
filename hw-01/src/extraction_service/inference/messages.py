"""Common prompt serialization for both model backends."""

import json

from extraction_service.inference.types import GenerationRequest


def request_messages(request: GenerationRequest) -> list[dict[str, str]]:
    """Show both models the same instructions, schema and neutral source text."""

    schema_text = json.dumps(request.output_schema, ensure_ascii=False, allow_nan=False)
    instructions = f"{request.instructions}\n\nJSON Schema:\n{schema_text}"

    return [
        {"role": "system", "content": instructions},
        {"role": "user", "content": request.source_text},
    ]
