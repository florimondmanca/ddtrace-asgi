from typing import Dict, Sequence


def parse_tags_from_list(tags: Sequence[str]) -> Dict[str, str]:
    parsed: Dict[str, str] = {}

    for tag in tags:
        name, _, value = tag.partition(":")
        parsed[name] = value

    return parsed
