from api.models import Finding, Source, Turn


def test_a_finding_with_no_data_is_not_ok():
    assert Finding(summary="Timed out.", data={}).ok is False
    assert Finding(summary="46 mm.", data={"rainfall_mm": 46.0}).ok is True


def test_a_knowledge_finding_knows_whether_the_guides_cover_the_question():
    assert Finding(summary="Not covered.", data={"found": False}).covered is False
    assert Finding(summary="Weather.", data={"rainfall_mm": 46.0}).covered is True  # only knowledge sets "found"


def test_a_turn_knows_its_field_and_every_source_it_cited():
    passage = Source(id="cg-06-3", source="CG-06.pdf", page=3, text="")
    turn = Turn(
        message="Should I spray?",
        answer="Wait.",
        tools_called=[],
        requirements={"field_id": "SL-PADDY-MINNERIYA"},
        findings={"knowledge": Finding(summary="Wait.", data={"found": True}, sources=[passage])},
    )
    assert turn.field_id == "SL-PADDY-MINNERIYA" and turn.sources == [passage]
    assert Turn(message="Hi", answer="Hello.", tools_called=[]).field_id is None
