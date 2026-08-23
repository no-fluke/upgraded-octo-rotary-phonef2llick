from os import environ
from typing import Dict, Optional


class TokenParser:
    def __init__(self, config_file: Optional[str] = None):
        """
        Initializes the TokenParser class.

        :param config_file: Optional path to a config file (currently unused).
        """
        self.tokens: Dict[int, str] = {}
        self.config_file = config_file  # Reserved for future use

    def parse_from_env(self) -> Dict[int, str]:
        """
        Parses all environment variables that start with 'MULTI_TOKEN'
        and returns them as a dictionary with 1-based integer keys.

        Example:
        MULTI_TOKEN1 = 123:ABC
        MULTI_TOKEN2 = 456:XYZ
        =>
        {
            1: "123:ABC",
            2: "456:XYZ"
        }

        :return: Dictionary of token mappings
        """
        self.tokens = {
            idx + 1: value
            for idx, (key, value) in enumerate(environ.items())
            if key.startswith("MULTI_TOKEN") and value.strip() != ""
        }
        return self.tokens
