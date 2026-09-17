from edb_agent.diffing import content_diff, human_summary


def test_detects_one_sentence_change() -> None:
    old = "概覽\n學校提供六年小學教育。\n其他資料"
    new = "概覽\n學校提供六年免費小學教育。\n其他資料"

    added, removed = content_diff(old, new)

    assert added == ["學校提供六年免費小學教育。"]
    assert removed == ["學校提供六年小學教育。"]
    summary = human_summary("小學教育", added, removed)
    assert "小學教育" in summary
    assert "新增：" in summary
    assert "移除：" in summary


def test_formatting_only_change_is_ignored_after_normalization() -> None:
    added, removed = content_diff("小學  教育\n\n資料", "小學 教育\n\n\n資料")
    assert added == []
    assert removed == []
