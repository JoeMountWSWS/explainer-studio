import pytest

from studio.common import DEFAULTS


def test_parses_scenes_notes_cues_and_pauses(write_script):
    script = write_script("""
        ---
        title: The Paris Commune
        paragraph_gap: 0.5
        ---
        # Working title (not narration)
        <!-- a comment {ignored} -->

        ## hook: Seventy-two days
        > template: title
        > duration: 4s
        > Red flag over the Hôtel de Ville.

        It lasted {days} seventy-two days.
        A second line of the same paragraph. {pause 1.5} After the pause.

        New paragraph.

        ## lesson: The lesson
        One {big idea} here.
    """)
    assert script.meta["title"] == "The Paris Commune"
    hook, lesson = script.scenes
    assert (hook.id, hook.title, hook.template, hook.min_duration) == ("hook", "Seventy-two days", "title", 4.0)
    assert hook.notes == ["Red flag over the Hôtel de Ville."]
    assert [c.words for c in hook.chunks] == [
        ["It", "lasted", "seventy-two", "days.", "A", "second", "line", "of", "the", "same", "paragraph."],
        ["After", "the", "pause."],
        ["New", "paragraph."],
    ]
    assert [c.gap_after for c in hook.chunks] == [1.5, 0.5, 0.0]  # the scene's last gap is always 0
    assert hook.cues == {"days": 2}
    assert hook.words[hook.cues["days"]] == "seventy-two"
    assert lesson.template == "blank"
    assert lesson.cues == {"big-idea": 1}  # spaces in a cue name become hyphens
    assert lesson.text == "One here."


def test_leading_pause_extends_previous_gap_and_default_pause_is_one_second(write_script):
    script = write_script("""
        ## a: A
        First.

        {pause} Second.
    """)
    assert [c.gap_after for c in script.scenes[0].chunks] == [DEFAULTS["paragraph_gap"] + 1.0, 0.0]


def test_silent_scene_with_duration(write_script):
    script = write_script("""
        ## card: Card
        > duration: 3
    """)
    assert script.scenes[0].chunks == []
    assert script.scenes[0].min_duration == 3.0


def test_setting_falls_back_to_defaults(write_script):
    script = write_script("""
        ---
        speed: 1.1
        ---
        ## a: A
        Words.
    """)
    assert script.setting("speed") == 1.1
    assert script.setting("fps") == DEFAULTS["fps"]
    assert script.setting("no-such-setting") is None


def test_no_front_matter(write_script):
    assert write_script("## a: A\nHello.\n").meta == {}


@pytest.mark.parametrize("body, message", [
    ("## Hook: A\nWords.\n", "must start with a lowercase letter"),
    ("## a: A\nOne.\n## a: B\nTwo.\n", "duplicate scene id"),
    ("## a: A\n{x} one {x} two.\n", "used twice"),
    ("## a: A\nOne {pause soon} two.\n", "bad pause marker"),
    ("## a: A\n> just a note\n", "has no narration"),
    ("Just prose, no headings.\n", "no scenes found"),
])
def test_errors(write_script, capsys, body, message):
    with pytest.raises(SystemExit):
        write_script(body)
    assert message in capsys.readouterr().err
