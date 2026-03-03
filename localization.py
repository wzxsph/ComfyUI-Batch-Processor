"""
Localization module for ComfyUI Batch Processor Pro.
Provides language switching between English and Chinese.
"""

import json
from pathlib import Path


class Localizer:
    """Manages translations and language switching."""

    SUPPORTED_LANGUAGES = {"en": "English", "zh": "中文"}

    def __init__(self, default_language="en"):
        self.translations_dir = Path(__file__).parent / "translations"
        self.current_language = default_language
        self.translations = {}
        self.config_file = Path(__file__).parent / "language_config.json"

        # Load saved language preference
        self._load_config()

        # Load translations
        self._load_translations()

    def _load_config(self):
        """Load saved language preference from config file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    saved_lang = config.get("language", "en")
                    if saved_lang in self.SUPPORTED_LANGUAGES:
                        self.current_language = saved_lang
            except Exception as e:
                print(f"Warning: Could not load language config: {e}")

    def _save_config(self):
        """Save current language preference to config file."""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(
                    {"language": self.current_language}, f, ensure_ascii=False, indent=2
                )
        except Exception as e:
            print(f"Warning: Could not save language config: {e}")

    def _load_translations(self):
        """Load translation files for all supported languages."""
        self.translations = {}
        for lang_code in self.SUPPORTED_LANGUAGES:
            trans_file = self.translations_dir / f"{lang_code}.json"
            if trans_file.exists():
                try:
                    with open(trans_file, "r", encoding="utf-8") as f:
                        self.translations[lang_code] = json.load(f)
                except Exception as e:
                    print(f"Error loading translations for {lang_code}: {e}")
                    self.translations[lang_code] = {}
            else:
                print(f"Warning: Translation file not found: {trans_file}")
                self.translations[lang_code] = {}

    def get_text(self, key, **kwargs):
        """
        Get translated text for a key in the current language.

        Args:
            key: Translation key
            **kwargs: Format arguments for string formatting

        Returns:
            Translated and formatted string, or the key itself if not found
        """
        text = self.translations.get(self.current_language, {}).get(key, key)

        # Format string if kwargs provided
        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, ValueError) as e:
                print(f"Warning: Failed to format text for key '{key}': {e}")

        return text

    def set_language(self, lang_code):
        """
        Change the current language.

        Args:
            lang_code: Language code ('en' or 'zh')

        Returns:
            bool: True if language was changed, False otherwise
        """
        if lang_code in self.SUPPORTED_LANGUAGES:
            if self.current_language != lang_code:
                self.current_language = lang_code
                self._save_config()
                return True
        return False

    def get_current_language(self):
        """Get the current language code."""
        return self.current_language

    def get_language_name(self, lang_code=None):
        """Get the display name of a language."""
        if lang_code is None:
            lang_code = self.current_language
        return self.SUPPORTED_LANGUAGES.get(lang_code, lang_code)


# Global localizer instance
_localizer = None


def init_localizer(default_language="en"):
    """Initialize the global localizer instance."""
    global _localizer
    _localizer = Localizer(default_language)
    return _localizer


def get_localizer():
    """Get the global localizer instance, creating it if necessary."""
    global _localizer
    if _localizer is None:
        _localizer = Localizer()
    return _localizer


def t(key, **kwargs):
    """
    Shorthand function to get translated text.

    Args:
        key: Translation key
        **kwargs: Format arguments for string formatting

    Returns:
        Translated and formatted string
    """
    return get_localizer().get_text(key, **kwargs)
