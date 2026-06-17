"""Project Memory frontmatter parser and renderer."""

from __future__ import annotations

import re

from metadata_defaults import REQUIRED_FIELDS


def parse_frontmatter(
    text: str,
) -> tuple[dict[str, object], str, bool]:
    stripped = text.lstrip("\n")
    if not stripped.startswith("---"):
        return {}, text, False

    rest = stripped[3:]
    if rest.startswith("\n"):
        rest = rest[1:]

    match = re.compile(r"^---[ \t]*$", re.MULTILINE).search(rest)
    if match is None:
        return {}, text, False

    yaml_block = rest[: match.start()]
    body = rest[match.end() :]
    if body.startswith("\n"):
        body = body[1:]

    return _parse_yaml_block(yaml_block), body, True


def _parse_yaml_block(block: str) -> dict[str, object]:
    result: dict[str, object] = {}
    current_key: str | None = None
    current_list: list[str] | None = None

    for raw_line in block.split("\n"):
        if _is_ignored_yaml_line(raw_line):
            continue

        list_value = _parse_list_item(raw_line)
        if list_value is not None and current_key is not None:
            current_list = _append_list_value(
                result, current_key, current_list, list_value
            )
            continue

        parsed_pair = _parse_key_value(raw_line)
        if parsed_pair is not None:
            current_key, raw_value = parsed_pair
            result[current_key] = _normalize_scalar_value(
                current_key, raw_value
            )
            current_list = None
            continue

        _reject_nested_yaml(raw_line, current_key)

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
        if double_quoted or single_quoted:
            return value[1:-1]
    return value


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
            lines.append(f"  - {item}")
    elif value is None:
        lines.append(f"{key}:")
    else:
        lines.append(f"{key}: {value}")
