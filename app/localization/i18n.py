"""Localization service loading translation catalogs with fallback support."""

import json
from pathlib import Path
from typing import Any, Dict
from app.core.config import settings
from app.core.constants import SupportedLanguage
from app.core.logging import logger

_LOCALES_DIR = Path(__file__).parent


class I18nService:
    """Translation manager supporting UZ, EN, and RU with automatic fallback."""

    def __init__(self, locales_dir: Path = _LOCALES_DIR):
        self.locales_dir = locales_dir
        self.translations: Dict[str, Dict[str, str]] = {}
        self._load_catalogs()

    def _load_catalogs(self) -> None:
        for lang in [SupportedLanguage.UZ.value, SupportedLanguage.EN.value, SupportedLanguage.RU.value]:
            file_path = self.locales_dir / f"{lang}.json"
            if file_path.exists():
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        self.translations[lang] = json.load(f)
                except Exception as e:
                    logger.error(f"Failed to load localization file for {lang}: {e}")
                    self.translations[lang] = {}
            else:
                logger.warning(f"Localization file {file_path} not found.")
                self.translations[lang] = {}

    def get(self, key: str, lang: str | None = None, **kwargs: Any) -> str:
        """Get translated message with variable formatting and fallback."""
        target_lang = (lang or settings.DEFAULT_LANGUAGE).lower()
        if target_lang not in self.translations:
            target_lang = settings.DEFAULT_LANGUAGE

        # Lookup in target language
        text = self.translations.get(target_lang, {}).get(key)

        # Fallback to default (uz)
        if text is None:
            text = self.translations.get(settings.DEFAULT_LANGUAGE, {}).get(key)

        # Fallback to English
        if text is None:
            text = self.translations.get("en", {}).get(key)

        # Fallback to key
        if text is None:
            text = key

        if kwargs:
            try:
                return text.format(**kwargs)
            except (KeyError, ValueError, IndexError):
                return text

        return text


# Global localization instance
i18n = I18nService()
