"""Tests for dhwani core functionality."""

import pytest
from dhvani.core import normalize, to_ipa, to_devanagari, are_same, identify_languages


class TestAreSame:
    """Test phonetic equivalence detection."""

    def test_bahut_variants(self):
        assert are_same("bahut", "bohot")
        assert are_same("bahut", "boht")
        assert are_same("bohot", "bahot")

    def test_accha_variants(self):
        assert are_same("accha", "achha")
        assert are_same("accha", "acha")

    def test_different_words(self):
        assert not are_same("bahut", "accha")
        assert not are_same("ghar", "kaam")

    def test_yaar_variants(self):
        assert are_same("yaar", "yar")


class TestIdentifyLanguages:
    """Test word-level language identification."""

    def test_mixed_sentence(self):
        result = identify_languages("bohot acha movie thi yaar")
        words, langs = zip(*result)
        assert langs[0] == "hi"  # bohot
        assert langs[2] == "en"  # movie
        assert langs[4] == "hi"  # yaar

    def test_devanagari(self):
        result = identify_languages("यह बहुत अच्छा है")
        _, langs = zip(*result)
        assert all(l == "hi_dev" for l in langs)


class TestNormalize:
    """Test normalization to different targets."""

    def test_to_ipa_basic(self):
        ipa = to_ipa("bahut")
        assert ipa  # should produce non-empty IPA
        assert "b" in ipa

    def test_to_devanagari(self):
        result = to_devanagari("namaste")
        assert result  # should produce something


class TestToDevanagari:
    """Test transliteration to Devanagari."""

    def test_basic_word(self):
        result = to_devanagari("kaam")
        assert result  # non-empty output
