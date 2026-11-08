"""Project Memory frontmatter parser and renderer."""

from __future__ import annotations

from enum import Enum, auto
import json
import re

from metadata_defaults import REQUIRED_FIELDS


class _FieldState(Enum):
    NO_KEY = auto()
    EMPTY = auto()
    SCALAR = auto()
    LIST = auto()


def parse_frontmatter(
    text: str,
) -> tuple[dict[str, object], str, bool]:
    stripped = text.lstrip("\n")
    opening = re.match(r"^---[ \t]*(?:\n|$)", stripped)
    if opening is None:
        return {}, text, False

    rest = stripped[opening.end() :]

    match = re.compile(r"^---[ \t]*$", re.MULTILINE).search(rest)
    if match is None:
        raise ValueError("Unterminated YAML frontmatter: missing closing delimiter")

    yaml_block = rest[: match.start()]
    body = rest[match.end() :]
    if body.startswith("\n"):
        body = body[1:]

    return _parse_yaml_block(yaml_block), body, True


def _parse_yaml_block(block: str) -> dict[str, object]:
    result: dict[str, object] = {}
    current_key: str | None = None
    current_list: list[str] | None = None
    state = _FieldState.NO_KEY
    list_indent: str | None = None

    for raw_line in block.split("\n"):
        if _is_ignored_yaml_line(raw_line):
            continue

        list_value = _parse_list_item(raw_line)
        if list_value is not None:
            if state is _FieldState.NO_KEY:
                raise ValueError("Unsupported YAML list without a key")
            if state is _FieldState.SCALAR:
                raise ValueError("Unsupported YAML list after a scalar value")
            indent = raw_line[: len(raw_line) - len(raw_line.lstrip(" \t"))]
            if state is _FieldState.LIST and indent != list_indent:
                raise ValueError("Unsupported nested YAML list indentation")
            assert current_key is not None
            current_list = _append_list_value(
                result, current_key, current_list, list_value
            )
            state = _FieldState.LIST
            list_indent = indent
            continue

        parsed_pair = _parse_key_value(raw_line)
        if parsed_pair is not None:
            current_key, raw_value = parsed_pair
            if current_key in result:
                raise ValueError(f"Duplicate YAML key: {current_key}")
            result[current_key] = _normalize_scalar_value(
                current_key, raw_value
            )
            current_list = None
            list_indent = None
            state = _FieldState.EMPTY if raw_value == "" else _FieldState.SCALAR
            continue

        _reject_nested_yaml(raw_line, current_key)
        raise ValueError("Unsupported YAML syntax: unrecognized top-level line")

    return result


def _is_ignored_yaml_line(raw_line: str) -> bool:
    return raw_line.strip() == "" or raw_line.lstrip().startswith("#")


def _parse_list_item(raw_line: str) -> str | None:
    list_match = re.match(r"^[ \t]+- (.+)$", raw_line)
    if not list_match:
        return None
    return _strip_quotes(list_match.group(1).strip())


def _append_list_value(
    result: dict[str, object],
    key: str,
    current_list: list[str] | None,
    value: str,
) -> list[str]:
    values = [] if current_list is None else current_list
    values.append(value)
    result[key] = values
    return values


def _parse_key_value(raw_line: str) -> tuple[str, str] | None:
    kv_match = re.match(r"^(\w[\w-]*)[ \t]*:[ \t]*(.*)$", raw_line)
    if not kv_match:
        return None
    return kv_match.group(1), kv_match.group(2).strip()


def _normalize_scalar_value(key: str, raw_value: str) -> str | None:
    if raw_value.startswith("{") or raw_value.startswith("["):
        raise ValueError(
            f"Unsupported YAML syntax for key '{key}': "
            f"flow mappings/sequences are not supported"
        )
    if raw_value == "":
        return None
    return _strip_quotes(raw_value)


def _reject_nested_yaml(raw_line: str, current_key: str | None) -> None:
    if raw_line.startswith(("  ", "\t")) and current_key is not None:
        raise ValueError(f"Unsupported nested YAML under key '{current_key}'")


def _strip_quotes(value: str) -> str:
    if len(value) >= 2:
        double_quoted = value[0] == '"' and value[-1] == '"'
        single_quoted = value[0] == "'" and value[-1] == "'"
        if double_quoted:
            try:
                decoded = json.loads(value)
            except (ValueError, TypeError) as exc:
                raise ValueError("Unsupported double-quoted YAML scalar") from exc
            if any(0xD800 <= ord(char) <= 0xDFFF for char in decoded):
                raise ValueError("Unsupported unpaired Unicode surrogate")
            return decoded
        if single_quoted:
            inner = value[1:-1]
            if re.fullmatch(r"(?:[^']|'')*", inner) is None:
                raise ValueError("Unsupported single-quoted YAML scalar")
            return inner.replace("''", "'")
    return value


def _render_scalar(value: object) -> str:
    value = str(value)
    if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
        raise ValueError("Unsupported unpaired Unicode surrogate")
    if (
        not value
        or value != value.strip()
        or value[0] in "{}[],'\"#&*!|>%@`-?:"
        or ": " in value
        or value.endswith(":")
        or " #" in value
        or any(_requires_unicode_escape(char) for char in value)
    ):
        rendered = json.dumps(value, ensure_ascii=False)
        return "".join(
            f"\\u{ord(char):04x}" if _requires_unicode_escape(char) else char
            for char in rendered
        )
    return value


def _requires_unicode_escape(char: str) -> bool:
    codepoint = ord(char)
    return (
        codepoint < 32
        or 0x7F <= codepoint <= 0x9F
        or codepoint in (0x2028, 0x2029, 0xFFFE, 0xFFFF)
    )


def render_frontmatter(data: dict[str, object]) -> str:
    lines: list[str] = []

    for key in REQUIRED_FIELDS:
        if key in data:
            _render_field(lines, key, data[key])

    for key, value in data.items():
        if key not in REQUIRED_FIELDS:
            _render_field(lines, key, value)

    return "\n".join(lines) + "\n"


def _render_field(lines: list[str], key: str, value: object) -> None:
    if isinstance(value, list):
        lines.append(f"{key}:")
        for item in value:
            lines.append(f"  - {_render_scalar(item)}")
    elif value is None:
        lines.append(f"{key}:")
    else:
        lines.append(f"{key}: {_render_scalar(value)}")
