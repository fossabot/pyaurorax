"""
Class definition used for managing the response from an
API request
"""

import pprint
from pydantic import BaseModel
from typing import Dict, Any

# pdoc init
__pdoc__: Dict = {}


class AuroraXResponse(BaseModel):
    """
    AuroraX API response class
    """
    request: Any
    data: Any
    status_code: int

    def __str__(self) -> str:
        """
        String method

        Returns:
            string format of AuroraXResponse
        """
        return self.__repr__()

    def __repr__(self) -> str:
        """
        Object representation

        Returns:
            object representation of AuroraXResponse
        """
        return pprint.pformat(self.__dict__)
