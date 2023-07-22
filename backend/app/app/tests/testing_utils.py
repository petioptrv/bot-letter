import re
from typing import Optional, Dict, Any, Pattern

from aioresponses.compat import normalize_url, merge_params


def compile_url_matcher(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    allow_additional_params: bool = False,
) -> Pattern:
    normalized_url = normalize_url(url=merge_params(url=url, params=params))
    normalized_url_str = str(normalized_url)
    if "?" not in normalized_url_str and allow_additional_params:
        normalized_url_str += "?"
    regex_str = f"^{normalized_url_str}".replace(".", r"\.").replace("?", r"\?")
    if allow_additional_params:
        initial_param_matcher = r"([\w\d=%-]*(&?))?"
        params_matcher = r"(&[\w\d=%-]*(&?))*"
        regex_base_str, regex_params_str = regex_str.split("?")
        regex_str = (
            regex_base_str
            + "?"
            + initial_param_matcher
            + params_matcher
            + params_matcher.join(regex_params_str.split("&"))
            + params_matcher
        )
    regex_url = re.compile(regex_str)
    return regex_url
