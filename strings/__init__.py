"""Language strings loader for IDOL Music."""
from __future__ import annotations

from strings import en
from strings import id as id_lang

_LANGUAGES = {
    "en": en,
    "id": id_lang,
}

DEFAULT_LANG = "en"


def get(key: str, lang: str = "en", **kwargs) -> str:
    """Get a localized string by key.

    Falls back to English if the key is missing in the target language.
    Supports format kwargs: get("NOW_PLAYING", "id", title="...", duration="...")
    """
    module = _LANGUAGES.get(lang, _LANGUAGES[DEFAULT_LANG])
    text = getattr(module, key, None)
    if text is None:
        text = getattr(en, key, f"[missing: {key}]")
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return text


def available_languages() -> list[str]:
    return list(_LANGUAGES.keys())
