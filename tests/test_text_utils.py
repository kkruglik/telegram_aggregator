import pytest
from app.utils.text import matches_keywords, find_matched_keyword


# ---------------------------------------------------------------------------
# Single words — basic morphology
# ---------------------------------------------------------------------------

def test_exact_nominative_match():
    assert matches_keywords("суд вынес приговор", {"суд"})


def test_genitive_form_matches_nominative_keyword():
    # "алкоголя" -> lemma "алкоголь"
    assert matches_keywords("продажу алкоголя запретили", {"алкоголь"})


def test_dative_form_matches():
    # "суду" -> lemma "суд"
    assert matches_keywords("передано суду для рассмотрения", {"суд"})


def test_instrumental_form_matches():
    # "судом" -> lemma "суд"
    assert matches_keywords("решение принято судом", {"суд"})


def test_plural_form_matches():
    # "суды" -> lemma "суд"
    assert matches_keywords("суды начали массово пресекать", {"суд"})


def test_verb_past_form_matches_keyword():
    # "задержан" is a short participle, lemma -> "задержать"
    assert matches_keywords("мужчина задержан полицией", {"задержан"})


def test_verb_declined_form_keyword():
    # keyword "задержан", text "задержали" — both -> "задержать"
    assert matches_keywords("полиция задержала преступника", {"задержан"})


def test_short_word_арест():
    assert matches_keywords("произведён арест имущества", {"арест"})


def test_declined_арест():
    # "арестован" -> "арестовать", keyword "арестован" -> "арестовать"
    assert matches_keywords("депутат арестован по решению суда", {"арестован"})


def test_keyword_убил():
    assert matches_keywords("мужчина убил соседа", {"убил"})


def test_keyword_убил_different_form():
    # "убили" -> "убить", "убил" -> "убить"
    assert matches_keywords("его убили вчера ночью", {"убил"})


# ---------------------------------------------------------------------------
# Short words — false positive prevention
# ---------------------------------------------------------------------------

def test_no_false_positive_суд_in_судьба():
    assert not matches_keywords("такова судьба", {"суд"})


def test_no_false_positive_суд_in_осуждён():
    # "осуждён" -> "осудить", "суд" -> "суд" — different lemmas
    assert not matches_keywords("он был осуждён", {"суд"})


def test_no_false_positive_суд_in_посудить():
    assert not matches_keywords("не стоит посудить об этом строго", {"суд"})


def test_no_false_positive_зек_in_незаконный():
    assert not matches_keywords("незаконный доступ к данным", {"зек"})


def test_no_false_positive_лгбт_in_unrelated():
    assert not matches_keywords("новые технологии изменят мир", {"лгбт"})


def test_no_false_positive_суд_in_судья():
    # "судья" -> "судья", "суд" -> "суд"
    assert not matches_keywords("судья огласил приговор", {"суд"})


# ---------------------------------------------------------------------------
# Long words
# ---------------------------------------------------------------------------

def test_long_keyword_законопроект():
    assert matches_keywords("в думе рассматривают законопроект об образовании", {"законопроект"})


def test_long_keyword_declined_form():
    # "законопроекта" -> "законопроект"
    assert matches_keywords("принятие законопроекта отложено", {"законопроект"})


def test_long_keyword_верховный_суд():
    # multi-word
    assert matches_keywords("верховный суд отменил решение", {"верховный суд"})


def test_long_keyword_постановление():
    assert matches_keywords("вышло новое постановление правительства", {"постановление"})


def test_long_keyword_постановление_declined():
    # "постановления" -> "постановление"
    assert matches_keywords("текст постановления опубликован", {"постановление"})


def test_long_keyword_мобилизация():
    assert matches_keywords("объявлена частичная мобилизация", {"мобилизация"})


def test_long_keyword_заключенный():
    assert matches_keywords("заключённый сбежал из колонии", {"заключенный"})


# ---------------------------------------------------------------------------
# Phrases (multi-word keywords)
# ---------------------------------------------------------------------------

def test_phrase_вернувшийся_с_фронта():
    assert matches_keywords("солдат вернулся с фронта домой", {"вернувшийся с фронта"})


def test_phrase_вернувшийся_с_фронта_partial_no_match():
    assert not matches_keywords("новости с фронта за сегодня", {"вернувшийся с фронта"})


def test_phrase_вернувшийся_с_сво():
    assert matches_keywords("ветеран вернулся с сво и открыл бизнес", {"вернувшийся с сво"})


def test_phrase_детские_сады():
    assert matches_keywords("детские сады закроют на карантин", {"детские сады"})


def test_phrase_детские_сады_declined():
    # "детских садов" -> lemmas детский, сад
    assert matches_keywords("нехватка мест в детских садах", {"детские сады"})


def test_phrase_верховный_суд():
    assert matches_keywords("верховный суд рассмотрит дело завтра", {"верховный суд"})


def test_phrase_решение_верховного_суда():
    assert matches_keywords("опубликовано решение верховного суда по делу", {"решение верховного суда"})


def test_phrase_ветеран_сво():
    assert matches_keywords("ветеран сво получил жильё", {"ветеран сво"})


def test_phrase_partial_words_not_enough():
    # phrase "ветеран сво" — only "ветеран" present
    assert not matches_keywords("ветеран войны рассказал о службе", {"ветеран сво"})


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_empty_keywords_passes_everything():
    assert matches_keywords("любой текст здесь", set())


def test_empty_text_no_match():
    assert not matches_keywords("", {"суд"})


def test_multiple_keywords_first_matches():
    assert matches_keywords("суд вынес приговор", {"алкоголь", "суд"})


def test_multiple_keywords_second_matches():
    assert matches_keywords("запрет алкоголя обсуждается", {"суд", "алкоголь"})


def test_multiple_keywords_none_match():
    assert not matches_keywords("спортивные результаты матча", {"алкоголь", "суд"})


def test_keyword_with_punctuation_in_text():
    # text has punctuation around the word
    assert matches_keywords("арестован. сообщает пресс-служба.", {"арестован"})


def test_case_insensitive_keyword():
    assert matches_keywords("Суд вынес решение", {"суд"})


def test_case_insensitive_text_and_keyword():
    assert matches_keywords("АРЕСТОВАН подозреваемый", {"арестован"})


# ---------------------------------------------------------------------------
# find_matched_keyword
# ---------------------------------------------------------------------------

def test_find_matched_keyword_returns_original_string():
    result = find_matched_keyword("продажу алкоголя запретили", {"алкоголь"})
    assert result == "алкоголь"


def test_find_matched_keyword_returns_none_on_no_match():
    assert find_matched_keyword("спортивные новости", {"алкоголь"}) is None


def test_find_matched_keyword_empty_keywords_returns_none():
    assert find_matched_keyword("любой текст", set()) is None


def test_find_matched_keyword_returns_phrase_as_typed():
    result = find_matched_keyword("солдат вернулся с фронта", {"вернувшийся с фронта"})
    assert result == "вернувшийся с фронта"


def test_find_matched_keyword_multiple_keywords_returns_one():
    result = find_matched_keyword("суд вынес приговор", {"алкоголь", "суд"})
    assert result == "суд"


def test_find_matched_keyword_no_false_positive():
    assert find_matched_keyword("такова судьба", {"суд"}) is None
