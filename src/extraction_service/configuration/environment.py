"""Reject retired environment names before settings can fall back to defaults."""

from pydantic_settings import BaseSettings, EnvSettingsSource, PydanticBaseSettingsSource


class ProjectSettings(BaseSettings):
    """Use the DI namespace and fail closed on stale process or dotenv settings."""

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Reject old names even when a new name is also supplied; never show values."""

        for source in (env_settings, dotenv_settings):
            if isinstance(source, EnvSettingsSource):
                if any(name.lower().startswith("hw01_") for name in source.env_vars):
                    raise ValueError("Retired HW01_ settings detected; migrate all names to DI_")

        return init_settings, env_settings, dotenv_settings, file_secret_settings
