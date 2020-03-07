from typing import Dict

import deprecation
from starlette.datastructures import CommaSeparatedStrings

from .._utils import parse_tags_from_list


@deprecation.deprecated(
    deprecated_in="0.4.0",
    removed_in="0.5.0",
    details=(
        "Pass a list or dict instead. "
        "Hint: use `starlette.datastructures.CommaSeparatedStrings` for parsing."
    ),
)
def parse_tags_from_string(value: str) -> Dict[str, str]:
    return parse_tags_from_list(CommaSeparatedStrings(value))
