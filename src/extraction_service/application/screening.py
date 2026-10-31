"""Validate the fixed labeled provider comparison before any client construction."""

from extraction_service.application.selection import RunOptions, select_models
from extraction_service.configuration.models import ExperimentConfig
from extraction_service.corpus.loading import LoadedCorpus
from extraction_service.record_types import ExecutionStage


def screening_options(
    experiment: ExperimentConfig, corpus: LoadedCorpus, options: RunOptions
) -> RunOptions:
    """Select exactly the gold input IDs with v1/baseline on explicit paid candidates."""

    if options.stage != ExecutionStage.SCREENING:
        return options

    gold_ids = [source.input_id for source in corpus.inputs if source.is_gold]

    if options.input_ids and (
        len(options.input_ids) != len(set(options.input_ids))
        or set(options.input_ids) != set(gold_ids)
    ):
        raise ValueError("Screening requires every approved gold input exactly once")

    if not options.model_ids or any(
        model.backend != "openrouter" for model in select_models(experiment, options)
    ):
        raise ValueError("Screening requires explicitly selected provider candidates")

    if options.prompt_ids not in ([], ["v1"]) or options.sampling_ids not in ([], ["baseline"]):
        raise ValueError("Screening requires unchanged v1/baseline selections")

    sampling = next((item for item in experiment.sampling if item.id == "baseline"), None)

    if sampling is None or sampling.temperature != 0.0 or sampling.top_p != 1.0:
        raise ValueError("Screening baseline requires temperature 0 and top_p 1")

    return options.model_copy(
        update={
            "input_ids": gold_ids,
            "prompt_ids": ["v1"],
            "sampling_ids": ["baseline"],
        }
    )
