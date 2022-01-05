import pyaurorax
import datetime
import pprint
from typing import Dict, List, Union
from ._ephemeris import Ephemeris

# pdoc init
__pdoc__: Dict = {}


class Search():
    """
    Class representing an AuroraX ephemeris search

    Note: At least one search criteria from programs, platforms, or instrument_types
    must be specified.

    Args:
        start: start timestamp of the search
        end: end timestamp of the search
        programs: list of programs to search through, defaults to None
        platforms: list of platforms to search through, defaults to None
        instrument_types: list of instrument types to search through, defaults to None
        metadata_filters: list of dictionaries describing metadata keys and
            values to filter on, defaults to None

            e.g. {
                "key": "string",
                "operator": "=",
                "values": [
                    "string"
                ]
            }
        verbose: output poll times, defaults to False
        poll_interval: time in seconds to wait between polling attempts, defaults
            to pyaurorax.requests.STANDARD_POLLING_SLEEP_TIME
        response_format: JSON representation of desired data response format
        request: pyaurorax.AuroraXResponse object returned when the search is executed
        request_id: unique AuroraX string ID assigned to the request
        request_url: unique AuroraX URL string assigned to the request
        executed: boolean, gets set to True when the search is executed
        completed: boolean, gets set to True when the search is checked to be finished
        data_url: the URL string where data is accessed
        query: dictionary of values sent for the search query
        status: dictionary of status updates
        data: list of pyaurorax.ephemeris.Ephemeris objects returned, or a list of
            raw JSON results if response_format is specified
        logs: list of logging messages from the API
    """

    def __init__(self,
                 start: datetime.datetime,
                 end: datetime.datetime,
                 programs: List[str] = None,
                 platforms: List[str] = None,
                 instrument_types: List[str] = None,
                 metadata_filters: List[Dict] = None,
                 response_format: Dict = None,
                 metadata_filters_logical_operator: str = "AND") -> None:

        self.request = None
        self.request_id = ""
        self.request_url = ""
        self.executed = False
        self.completed = False
        self.data_url = ""
        self.query = {}
        self.status = {}
        self.data: List[Union[Ephemeris, Dict]] = []
        self.logs = []

        self.start = start
        self.end = end
        self.programs = programs
        self.platforms = platforms
        self.instrument_types = instrument_types
        self.metadata_filters = metadata_filters
        self.metadata_filters_logical_operator = metadata_filters_logical_operator
        self.response_format = response_format

    def __str__(self) -> str:
        """
        String method

        Returns:
            string format of Ephemeris Search object
        """
        return self.__repr__()

    def __repr__(self) -> str:
        """
        Object representation

        Returns:
            object representation of Ephemeris Search object
        """
        return pprint.pformat(self.__dict__)

    def execute(self) -> None:
        """
        Initiate ephemeris search request

        Raises:
            pyaurorax.exceptions.AuroraXBadParametersException: missing parameters
        """
        # check for at least one filter criteria
        if not (self.programs or self.platforms or self.instrument_types or self.metadata_filters):
            raise pyaurorax.AuroraXBadParametersException("At least one filter criteria parameter "
                                                          "besides 'start' and 'end' must be specified")

        # set up request
        url = pyaurorax.api.urls.ephemeris_search_url
        post_data = {
            "data_sources": {
                "programs": [] if not self.programs else self.programs,
                "platforms": [] if not self.platforms else self.platforms,
                "instrument_types": [] if not self.instrument_types else self.instrument_types,
                "ephemeris_metadata_filters": {} if not self.metadata_filters
                else {
                    "logical_operator": self.metadata_filters_logical_operator,
                    "expressions": self.metadata_filters
                },
            },
            "start": self.start.strftime("%Y-%m-%dT%H:%M:%S"),
            "end": self.end.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        self.query = post_data

        # do request
        req = pyaurorax.AuroraXRequest(method="post",
                                       url=url,
                                       body=post_data,
                                       null_response=True)
        res = req.execute()

        # set request ID, request_url, executed
        self.executed = True
        if (res.status_code == 202):
            # request successfully dispatched
            self.executed = True
            self.request_url = res.request.headers["location"]
            self.request_id = self.request_url.rsplit("/", 1)[-1]
        self.request = res

    def update_status(self, status: Dict = None) -> None:
        """
        Update the status of this ephemeris search request

        Args:
            status: retrieved status dictionary (include to avoid requesting it
                from the API again), defaults to None
        """
        # get the status if it isn't passed in
        if (status is None):
            status = pyaurorax.requests.get_status(self.request_url)

        # update request status by checking if data URI is set
        if (status["search_result"]["data_uri"] is not None):
            self.completed = True
            self.data_url = "%s%s" % (pyaurorax.api.urls.base_url,
                                      status["search_result"]["data_uri"])

        # set class variable "status" and "logs"
        self.status = status
        self.logs = status["logs"]

    def check_for_data(self) -> bool:
        """
        Check to see if data is available for this ephemeris
        search request

        Returns:
            True if data is available, else False
        """
        self.update_status()
        return self.completed

    def get_data(self) -> None:
        """
        Retrieve the data available for this ephemeris search
        request
        """
        # check if completed yet
        if (self.completed is False):
            print("No data available, update status or check for data first")
            return

        # get data
        url = self.data_url
        raw_data = pyaurorax.requests.get_data(url,
                                               post_body=self.response_format)

        # set data variable
        if self.response_format is not None:
            self.data = raw_data
        else:
            self.data = [Ephemeris(**e) for e in raw_data]

    def wait(self,
             poll_interval: float = pyaurorax.requests.STANDARD_POLLING_SLEEP_TIME,
             verbose: bool = False) -> None:
        """
        Block and wait for the request to complete and data is
        available for retrieval

        Args:
            poll_interval: time in seconds to wait between polling attempts,
                defaults to pyaurorax.requests.STANDARD_POLLING_SLEEP_TIME
            verbose: output poll times, defaults to False
        """
        url = pyaurorax.api.urls.ephemeris_request_url.format(self.request_id)
        self.update_status(pyaurorax.requests.wait_for_data(url,
                                                            poll_interval=poll_interval,
                                                            verbose=verbose))

    def cancel(self,
               wait: bool = False,
               verbose: bool = False,
               poll_interval: float = pyaurorax.requests.STANDARD_POLLING_SLEEP_TIME) -> int:
        """
        Cancel the ephemeris search request at the API. This method returns
        asynchronously by default.

        Args:
            wait: set to True to block until the cancellation request
                has been completed (may wait for several minutes)
            verbose: if True then output poll times and other
                progress, defaults to False
            poll_interval: seconds to wait between polling
                calls, defaults to STANDARD_POLLING_SLEEP_TIME.

        Returns:
            1 on success

        Raises:
            pyaurorax.exceptions.AuroraXUnexpectedContentTypeException: unexpected error
            pyaurorax.exceptions.AuroraXUnauthorizedException: invalid API key for this operation
        """
        url = pyaurorax.api.urls.ephemeris_request_url.format(self.request_id)
        return pyaurorax.requests.cancel(url, wait=wait, poll_interval=poll_interval, verbose=verbose)
