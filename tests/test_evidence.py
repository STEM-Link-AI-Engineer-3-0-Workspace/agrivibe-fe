from api.models import Finding, Source
from presenters import evidence


def test_citations_become_numbers_or_the_guide_code():
    sources = [
        Source(id="cg-07-rice-35f25c-2", source="CG-07_rice.pdf", page=1, text=""),
        Source(id="cg-06-fert-1a12a4-3", source="CG-06_fert.pdf", page=3, text=""),
    ]
    text = evidence.cite("Bg 352 [cg-07-rice-35f25c-2]. Rates [cg-06-fert-5, cg-06-fert-9]. Other [zz-99-q]. Not [this].", sources)

    assert text == "Bg 352 [1]. Rates [2]. Other [ZZ-99]. Not [this]."


def test_a_knowledge_question_the_guides_do_not_cover_says_so():
    assert evidence.status(Finding(summary="Not covered.", data={"found": False})) == "Not in the guides"


def test_data_keys_read_as_plain_words():
    assert evidence.metric("rainfall_last_7_days_mm", 112.0) == ("Rainfall last 7 days", "112 mm")
    assert evidence.metric("ndvi_change_percentage", -15.2) == ("NDVI change", "-15.2%")
    assert evidence.metric("current_mean_ndvi", 0.56) == ("Current mean NDVI", "0.56")
    assert evidence.metric("trend", "significant_decline") == ("Trend", "significant decline")
    assert evidence.metric("heavy_rain_expected", True) == ("Heavy rain expected", "Yes")


def test_a_specialist_with_no_data_says_so():
    assert evidence.status(Finding(summary="Satellite timed out.", data={})) == "No data"
    assert evidence.status(Finding(summary="46 mm.", data={"rainfall_mm": 46.0})) == "Done"
