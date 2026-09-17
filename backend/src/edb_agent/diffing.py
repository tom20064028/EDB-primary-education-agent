from __future__ import annotations

from difflib import SequenceMatcher

from .extractor import normalize_text


def content_diff(old_content: str, new_content: str) -> tuple[list[str], list[str]]:
    old_lines = [line for line in normalize_text(old_content).splitlines() if line]
    new_lines = [line for line in normalize_text(new_content).splitlines() if line]
    matcher = SequenceMatcher(a=old_lines, b=new_lines, autojunk=False)
    added: list[str] = []
    removed: list[str] = []
    for operation, old_start, old_end, new_start, new_end in matcher.get_opcodes():
        if operation in {"replace", "delete"}:
            removed.extend(old_lines[old_start:old_end])
        if operation in {"replace", "insert"}:
            added.extend(new_lines[new_start:new_end])
    return added, removed


def human_summary(page_title: str, added: list[str], removed: list[str]) -> str:
    if added and removed:
        lead = (
            f"{page_title} 有內容更新：修改或移除了 {len(removed)} 項，並新增了 {len(added)} 項。"
        )
    elif added:
        lead = f"{page_title} 新增了 {len(added)} 項內容。"
    elif removed:
        lead = f"{page_title} 移除了 {len(removed)} 項內容。"
    else:
        return f"{page_title} 有內容變更，但未能抽取可讀的文字差異。"

    details: list[str] = []
    if added:
        details.append(f"新增：「{added[0][:240]}」")
    if removed:
        details.append(f"移除：「{removed[0][:240]}」")
    return " ".join([lead, *details])
