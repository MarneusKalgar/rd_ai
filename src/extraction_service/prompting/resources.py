"""Load pinned skill content into complete instructions without model-driven discovery."""

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Literal

from extraction_service.artifacts import ArtifactError, artifact_path, read_checked, read_text
from extraction_service.configuration.models import PromptConfig, PromptResource
from extraction_service.runtime_types import NonEmptyText, Sha256, StrictModel

RESOURCE_VERSION: Final = "prompt-skill-resources-v1"
SKILL_SEPARATOR: Final[str] = "\n\nAPPLICATION-LOADED PROMPT RESOURCES\n"


class LoadedResource(StrictModel):
    file: NonEmptyText
    sha256: Sha256
    content: NonEmptyText


class PromptEvidence(StrictModel):
    version: Literal["prompt-skill-resources-v1"] = RESOURCE_VERSION
    base: LoadedResource
    loaded: list[LoadedResource]
    rendered_text: NonEmptyText
    rendered_sha256: Sha256


@dataclass(frozen=True)
class LoadedPrompt:
    instructions: str
    evidence: PromptEvidence | None = None


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _render(base: str, loaded: list[LoadedResource]) -> str:
    """Keep the original prefix exact; resource order is explicit and reproducible."""

    return base + SKILL_SEPARATOR + "\n\n".join(resource.content for resource in loaded)


def load_prompt(project: Path, prompt: PromptConfig) -> LoadedPrompt:
    """Read public prompt files only, verifying every requested package byte hash.

    References inside content are inert. Only configured resources are loaded;
    missing/changed files or paths outside the package fail before model setup.
    """

    prompt_root = (project / "prompts").resolve()
    base_path = artifact_path(project, prompt.file)
    if not base_path.is_relative_to(prompt_root):
        raise ArtifactError("Referenced prompt must belong to the project's prompts directory")
    base = read_text(base_path)
    if not base.strip():
        raise ArtifactError("Referenced prompt cannot be empty")
    if prompt.skill is None:
        return LoadedPrompt(base)

    skill = prompt.skill
    skill_path = artifact_path(project, skill.file)
    if skill_path.name != "SKILL.md" or not skill_path.is_relative_to(prompt_root / "skills"):
        raise ArtifactError("Skill must be a SKILL.md in prompts/skills")
    if base_path.is_relative_to(skill_path.parent):
        raise ArtifactError("Base prompt must be separate from its example package")
    references = [PromptResource(file=skill.file, sha256=skill.sha256), *skill.resources]
    loaded = []
    resolved: set[Path] = set()
    for resource in references:
        path = artifact_path(project, resource.file)
        if not path.is_relative_to(skill_path.parent) or path in resolved:
            raise ArtifactError("Skill resource must be unique and stay within its package")
        resolved.add(path)
        content = read_checked(path, resource.sha256)
        if not content.strip():
            raise ArtifactError("Skill resource cannot be empty")
        loaded.append(LoadedResource(file=resource.file, sha256=resource.sha256, content=content))
    rendered = _render(base, loaded)
    evidence = PromptEvidence(
        base=LoadedResource(file=prompt.file, sha256=_digest(base), content=base),
        loaded=loaded,
        rendered_text=rendered,
        rendered_sha256=_digest(rendered),
    )
    return LoadedPrompt(rendered, evidence)


def validate_prompt_evidence(value: dict[str, Any], prompt: PromptConfig) -> str:
    """Reconstruct archived instruction bytes without accessing resource files or gold."""

    evidence = PromptEvidence.model_validate(value)
    if prompt.skill is None:
        raise ValueError("Plain prompt cannot declare skill resources")
    expected = [(prompt.skill.file, prompt.skill.sha256)]
    expected.extend((resource.file, resource.sha256) for resource in prompt.skill.resources)
    actual = [(resource.file, resource.sha256) for resource in evidence.loaded]
    if evidence.base.file != prompt.file or actual != expected:
        raise ValueError("Saved skill resource selection/order differs from configuration")
    for resource in [evidence.base, *evidence.loaded]:
        if _digest(resource.content) != resource.sha256:
            raise ValueError("Saved skill content hash differs")
    rendered = _render(evidence.base.content, evidence.loaded)
    if rendered != evidence.rendered_text or _digest(rendered) != evidence.rendered_sha256:
        raise ValueError("Saved rendered skill instructions differ")
    return rendered
