"""
Class definition for an ephemeris search
"""

import datetime
from typing import Dict, List, Union, Optional
from .ephemeris import Ephemeris
from ...api import AuroraXRequest, AuroraXResponse, urls
from ...sources import DataSource, FORMAT_BASIC_INFO
from ...exceptions import (AuroraXBadParametersException)
from ...requests import (STANDARD_POLLING_SLEEP_TIME,
                         cancel as requests_cancel,
                         wait_for_data as requests_wait_for_data,
                         get_data as requests_get_data,
                         get_status as requests_get_status)

# pdoc init
__pdoc__: Dict = {}


class Search():
    """
    Class representing an ephemeris search

    Note: At least one search criteria from programs, platforms, or instrument_types
    must be specified.

    Args:
        start: start timestamp of the search (inclusive)
        end: end timestamp of the search (inclusive)
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
        metadata_filters_logical_operator: the logical operator to use when
            evaluating metadata filters (either 'AND' or 'OR'), defaults
            to "AND"
        response_format: JSON representation of desired data response format
        request: AuroraXResponse object returned when the search is executed
        request_id: unique ID assigned to the request by the AuroraX API
        request_url: unique URL assigned to the request by the AuroraX API
        executed: indicates if the search has been executed/started
        completed: indicates if the search has finished
        data_url: the URL where data is accessed
        query: the query for this request as JSON
        status: the status of the query
        data: the ephemeris records found
        logs: all log messages outputed by the AuroraX API for this request
    """

    def __init__(self,
                 start: datetime.datetime,
                 end: datetime.datetime,
                 programs: Optional[List[str]] = None,
                 platforms: Optional[List[str]] = None,
                 instrument_types: Optional[List[str]] = None,
                 metadata_filters: Optional[List[Dict]] = None,
                 metadata_filters_logical_operator: Optional[str] = "AND",
                 response_format: Optional[Dict] = None) -> None:

        # set variables using passed in args
        self.start = start
        self.end = end
        self.programs = programs
        self.platforms = platforms
        self.instrument_types = instrument_types
        self.metadata_filters = metadata_filters
        self.metadata_filters_logical_operator = metadata_filters_logical_operator
        self.response_format = response_format

        # initialize additional variables
        self.request: AuroraXResponse = None
        self.request_id: str = ""
        self.request_url: str = ""
        self.executed: bool = False
        self.completed: bool = False
        self.data_url: str = ""
        self.query: Dict = {}
        self.status: Dict = {}
        self.data: List[Union[Ephemeris, Dict]] = []
        self.logs: List[Dict] = []

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
        return f"EphemerisSearch(executed={self.executed}, " \
            f"completed={self.completed}, request_id='{self.request_id}')"

    @property
    def query(self):
        """
        Property for the query value
        """
        self._query = {
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
        return self._query

    @query.setter
    def query(self, query):
        self._query = query

    def execute(self) -> None:
        """
        Initiate ephemeris search request

        Raises:
            pyaurorax.exceptions.AuroraXBadParametersException: missing parameters
        """
        # check for at least one filter criteria
        if not (self.programs or self.platforms or self.instrument_types or self.metadata_filters):
            raise AuroraXBadParametersException("At least one filter criteria parameter "
                                                "besides 'start' and 'end' must be specified")

        # do request
        url = urls.ephemeris_search_url
        req = AuroraXRequest(method="post",
                             url=url,
                             body=self.query,
                             null_response=True)
        res = req.execute()

        # set request ID, request_url, executed
        self.executed = True
        if (res.status_code == 202):
            # request successfully dispatched
            self.executed = True
            self.request_url = res.request.headers["location"]
            self.request_id = self.request_url.rsplit("/", 1)[-1]

        # set the request variable
        self.request = res

    def update_status(self, status: Optional[Dict] = None) -> None:
        """
        Update the status of this ephemeris search request

        Args:
            status: the previously-retrieved status of this request (include
                to avoid requesting it from the API again), defaults to None
        """
        # get the status if it isn't passed in
        if (status is None):
            status = requests_get_status(self.request_url)

        # update request status by checking if data URI is set
        if (status["search_result"]["data_uri"] is not None):
            self.completed = True
            self.data_url = "%s%s" % (urls.base_url,
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
        raw_data = requests_get_data(self.data_url, response_format=self.response_format)

        # set data variable
        if self.response_format is not None:
            self.data = raw_data
        else:
            # cast data source objects
            for i in range(0, len(raw_data)):
                ds = DataSource(**raw_data[i]["data_source"], format=FORMAT_BASIC_INFO)
                raw_data[i]["data_source"] = ds

            # cast ephemeris objects
            self.data = [Ephemeris(**e) for e in raw_data]

    def wait(self,
             poll_interval: Optional[float] = STANDARD_POLLING_SLEEP_TIME,
             verbose: Optional[bool] = False) -> None:
        """
        Block and wait for the request to complete and data is
        available for retrieval

        Args:
            poll_interval: time in seconds to wait between polling attempts,
                defaults to pyaurorax.requests.STANDARD_POLLING_SLEEP_TIME
            verbose: output poll times and other progress messages, defaults
                to False
        """
        url = urls.ephemeris_request_url.format(self.request_id)
        self.update_status(requests_wait_for_data(url,
                                                  poll_interval=poll_interval,
                                                  verbose=verbose))

    def cancel(self,
               wait: Optional[bool] = False,
               poll_interval: float = STANDARD_POLLING_SLEEP_TIME,
               verbose: Optional[bool] = False) -> int:
        """
        Cancel the ephemeris search request

        This method returns immediately by default since the API processes
        this request asynchronously. If you would prefer to wait for it
        to be completed, set the 'wait' parameter to True. You can adjust
        the polling time using the 'poll_interval' parameter.

        Args:
            wait: wait until the cancellation request has been
                completed (may wait for several minutes)
            poll_interval: seconds to wait between polling
                calls, defaults to STANDARD_POLLING_SLEEP_TIME.
            verbose: output poll times and other progress messages, defaults
                to False

        Returns:
            1 on success

        Raises:
            pyaurorax.exceptions.AuroraXUnexpectedContentTypeException: unexpected error
            pyaurorax.exceptions.AuroraXUnauthorizedException: invalid API key for this operation
        """
        url = urls.ephemeris_request_url.format(self.request_id)
        return requests_cancel(url, wait=wait, poll_interval=poll_interval, verbose=verbose)
