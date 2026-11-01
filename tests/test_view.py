from datetime import UTC, datetime, timedelta

import ui
import view
from client import Finding, Source, ThreadSummary, Turn
from ui.primitives import badge, button

NOW = datetime(2026, 11, 1, 18, 0, tzinfo=UTC)


def summary(thread_id, title, days_ago):
    return ThreadSummary(thread_id=thread_id, title=title, updated_at=NOW - timedelta(days=days_ago), turns=1)


def test_text_from_agents_documents_and_the_farmer_cannot_inject_html():
    hostile = Turn(
        message="<img src=x onerror=alert(1)>",
        answer="<script>alert(1)</script> **bold**",
        tools_called=["ask_knowledge_agent", "<b>tool</b>"],
        requirements={"field_id": "<i>x</i>"},
        findings={
            "knowledge": Finding(
                summary="<svg onload=alert(1)>",
                data={"note": "<img src=x>"},
                sources=[Source(id="x", source="<b>evil</b>.pdf", page=1, text="<script>", rerank_score=None)],
            )
        },
    )
    page = view.conversation([hostile]) + view.thread_list([summary("t\"1", "<b>title</b>", 0)], None, NOW)

    for raw in ("<script>", "<img", "<svg onload", "<b>evil", "<b>tool", "<b>title", 't"1'):
        assert raw not in page
    assert "&lt;script&gt;" in page and "<strong>bold</strong>" in page


def test_citations_become_numbered_chips_or_the_guide_code():
    sources = [
        Source(id="cg-07-rice-35f25c-2", source="CG-07_rice.pdf", page=1, text=""),
        Source(id="cg-06-fert-1a12a4-3", source="CG-06_fert.pdf", page=3, text=""),
    ]
    html = view.cite("<p>Bg 352 [cg-07-rice-35f25c-2]. Rates [cg-06-fert-5, cg-06-fert-9]. Other [zz-99-q].</p>", sources)

    assert 'Bg 352<span class="citation" title="CG-07_rice.pdf · p. 1">1</span>.' in html
    assert html.count(">2</span>") == 1  # two passages of the same guide make one chip
    assert '<span class="citation" title="zz-99-q">ZZ-99</span>' in html  # cited, but not among the sources


def test_history_is_grouped_by_day_with_the_open_one_highlighted():
    threads = [summary("a", "Today's", 0), summary("b", "Yesterday's", 1), summary("c", "Last week's", 5), summary("d", "Old", 90)]

    html = view.thread_list(threads, active="b", now=NOW)

    assert html.index("Today") < html.index("Yesterday") < html.index("Previous 7 days") < html.index("Older")
    assert html.count("data-active") == 1 and html.index("data-active") < html.index("Yesterday&#x27;s")
    assert 'data-event="open" data-id="a"' in html and 'data-event="remove" data-id="a"' in html
    assert 'data-confirm="Delete “Today&#x27;s” and its evidence?"' in html


def test_an_empty_history_says_so():
    assert "will appear here" in view.thread_list([], None)


def test_a_knowledge_question_the_guides_do_not_cover_says_so():
    finding = Finding(summary="Not covered.", data={"found": False})
    assert "Not in the guides" in view.finding_status("knowledge", finding)


def test_data_keys_read_as_plain_words():
    assert view.metric("rainfall_last_7_days_mm", 112.0) == ("Rainfall last 7 days", "112 mm")
    assert view.metric("ndvi_change_percentage", -15.2) == ("NDVI change", "-15.2%")
    assert view.metric("current_mean_ndvi", 0.56) == ("Current mean NDVI", "0.56")
    assert view.metric("trend", "significant_decline") == ("Trend", "significant decline")
    assert view.metric("heavy_rain_expected", True) == ("Heavy rain expected", "Yes")


def test_primitives_take_shadcn_variants_and_escape_their_text():
    assert button("New chat", icon_name="square-pen", variant="outline", size="sm").startswith(
        '<button type="button" class="ui-button" data-variant="outline" data-size="sm">'
    )
    assert 'aria-label="Delete"' in button("Delete", icon_name="trash-2", size="icon-sm")
    assert badge("<b>x</b>", variant="warning") == '<span class="ui-badge" data-variant="warning">&lt;b&gt;x&lt;/b&gt;</span>'


def test_components_expose_their_events_to_python():
    # gr.HTML only lets Python listen to an event whose name is quoted in the component's JavaScript.
    assert callable(ui.Composer(placeholder="Ask", render=False).send)
    assert callable(ui.Conversation(render=False).suggest)
    history = ui.ThreadList(render=False)
    assert callable(history.open) and callable(history.remove)
