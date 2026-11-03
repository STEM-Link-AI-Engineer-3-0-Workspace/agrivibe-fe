from contracts import page


def test_the_header_names_the_conversation_field_and_backend():
    assert page.header(None, None, None) == "**New conversation**"
    assert page.header("Is *my* field ok?", "SL-1", True) == "**Is \\*my\\* field ok?**  \nField `SL-1` · Backend online"


def test_the_greeting_uses_the_first_name():
    assert page.greeting("Nimal Perera").startswith("## Hello, Nimal\n")
