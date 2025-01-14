"""
Class definition for a conjunction search
"""

import datetime
import itertools
from typing import Dict, List, Union, Optional
from .conjunction import Conjunction
from ...conjunctions import CONJUNCTION_TYPE_NBTRACE
from ...api import AuroraXRequest, AuroraXResponse, urls
from ...sources import DataSource, FORMAT_BASIC_INFO
from ...exceptions import AuroraXBadParametersException
from ...requests import (STANDARD_POLLING_SLEEP_TIME,
                         cancel as requests_cancel,
                         wait_for_data as requests_wait_for_data,
                         get_data as requests_get_data,
                         get_status as requests_get_status)

# pdoc init
__pdoc__: Dict = {}


class Search():
    """
    Class representing a conjunction search

    Attributes:
        start: start timestamp of the search (inclusive)
        end: end timestamp of the search (inclusive)
        distance: the maximum distance allowed between data sources when searching for
            conjunctions. This can either be a number (int or float), or a dictionary
            modified from the output of the "get_advanced_distances_combos()" function.
        ground: list of ground instrument search parameters, defaults to []

            Example:

                [{
                    "programs": ["themis-asi"],
                    "platforms": ["gillam", "rabbit lake"],
                    "instrument_types": ["RGB"],
                    "ephemeris_metadata_filters": {
                        "logical_operator": "AND",
                        "expressions": [
                            {
                                "key": "calgary_apa_ml_v1",
                                "operator": "in",
                                "values": [ "classified as APA" ]
                            }
                        ]
                    }
                }]
        space: list of one or more space instrument search parameters, defaults to []

            Example:

                [{
                    "programs": ["themis-asi", "swarm"],
                    "platforms": ["themisa", "swarma"],
                    "instrument_types": ["footprint"],
                    "ephemeris_metadata_filters": {
                        "logical_operator": "AND",
                        "expressions": [
                            {
                                "key": "nbtrace_region",
                                "operator": "in",
                                "values": [ "north auroral oval" ]
                            }
                        ]
                    },
                    "hemisphere": [
                        "northern"
                    ]
                }]
        events: list of one or more events search parameters, defaults to []

            Example:

                [{
                    "programs": [ "events" ],
                    "platforms": [ "toshi" ],
                    "instrument_types": [ "substorm onsets" ]
                }]
        conjunction_types: list of conjunction types, defaults to ["nbtrace"]. Options are
            in the pyaurorax.conjunctions module, or at the top level using the
            pyaurorax.CONJUNCTION_TYPE_* variables.
        epoch_search_precision: the time precision to which conjunctions are calculated. Can be
            30 or 60 seconds. Defaults to 60 seconds. Note - this parameter is under active
            development and still considered "alpha".
        response_format: JSON representation of desired data response format
        request: AuroraXResponse object returned when the search is executed
        request_id: unique ID assigned to the request by the AuroraX API
        request_url: unique URL assigned to the request by the AuroraX API
        executed: indicates if the search has been executed/started
        completed: indicates if the search has finished
        data_url: the URL where data is accessed
        query: the query for this request as JSON
        status: the status of the query
        data: the conjunctions found
        logs: all log messages outputed by the AuroraX API for this request

        Returns:
            a pyaurorax.conjunctions.Search object
    """

    def __init__(self, start: datetime.datetime,
                 end: datetime.datetime,
                 distance: Union[int, float, Dict[str, Union[int, float]]],
                 ground: Optional[List[Dict[str, str]]] = [],
                 space: Optional[List[Dict[str, str]]] = [],
                 events: Optional[List[Dict[str, str]]] = [],
                 conjunction_types: Optional[List[str]] = [CONJUNCTION_TYPE_NBTRACE],
                 epoch_search_precision: Optional[int] = 60,
                 response_format: Optional[Dict[str, bool]] = None):

        # set variables using passed in args
        self.start = start
        self.end = end
        self.ground = ground
        self.space = space
        self.events = events
        self.distance = distance
        self.conjunction_types = conjunction_types
        self.epoch_search_precision = epoch_search_precision
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
        self.data: List[Union[Conjunction, Dict]] = []
        self.logs: List[Dict] = []

    def __str__(self):
        """
        String method

        Returns:
            string format of Conjunction Search object
        """
        return self.__repr__()

    def __repr__(self):
        """
        Object representation

        Returns:
            object representation of Conjunction Search object
        """
        return f"ConjunctionSearch(executed={self.executed}, " \
            f"completed={self.completed}, request_id='{self.request_id}')"

    def check_criteria_block_count_validity(self) -> None:
        """
        Check the number of of criteria blocks to see if there
        is too many. A max of 10 is allowed by the AuroraX
        conjunction search engine. An exception is raised if
        it was determined to have too many.

        Raises:
            pyaurorax.exceptions.AuroraXBadParametersException: too many criteria blocks are found
        """
        if ((len(self.ground) + len(self.space) + len(self.events)) > 10):
            raise AuroraXBadParametersException("Number of criteria blocks exceeds 10, "
                                                "please reduce the count")

    def get_advanced_distances_combos(self, default_distance: Union[int, float] = None) -> Dict:
        """
        Get the advanced distances combinations for this search

        Args:
            default_distance: the default distance to use, defaults to None

        Returns:
            the advanced distances combinations
        """
        # set input arrays
        options = []
        for i in range(0, len(self.ground)):
            options.append("ground%d" % (i + 1))
        for i in range(0, len(self.space)):
            options.append("space%d" % (i + 1))
        for i in range(0, len(self.events)):
            options.append("events%d" % (i + 1))

        # derive all combinations of options of size 2
        combinations = {}
        for element in itertools.combinations(options, r=2):
            combinations["%s-%s" % (element[0], element[1])] = default_distance

        # return
        return combinations

    def __fill_in_missing_distances(self, curr_distances: Dict) -> Dict:
        # get all distances possible
        all_distances = self.get_advanced_distances_combos()

        # go through current distances and fill in the values
        for curr_key, curr_value in curr_distances.items():
            curr_key_split = curr_key.split('-')
            curr_key1 = curr_key_split[0].strip()
            curr_key2 = curr_key_split[1].strip()
            for all_key in all_distances.keys():
                if (curr_key1 in all_key and curr_key2 in all_key):
                    # found the matching key, replace the value
                    all_distances[all_key] = curr_value

        # return
        return all_distances

    @property
    def distance(self) -> Union[int, float, Dict[str, Union[int, float]]]:
        """
        Property for the distance parameter

        Returns:
            the distance dictionary with all combinations
        """
        return self._distance

    @distance.setter
    def distance(self, distance: Union[int, float, Dict[str, Union[int, float]]]) -> None:
        # set distances to a dict if it's an int or float
        if (type(distance) is int or type(distance) is float):
            self._distance = self.get_advanced_distances_combos(default_distance=distance)  # type: ignore
        else:
            # is a dict, fill in any gaps
            self._distance = self.__fill_in_missing_distances(distance)  # type: ignore

    @property
    def query(self) -> Dict:
        """
        Property for the query value

        Returns:
            the query parameter
        """
        self._query = {
            "start": self.start.strftime("%Y-%m-%dT%H:%M:%S"),
            "end": self.end.strftime("%Y-%m-%dT%H:%M:%S"),
            "ground": self.ground,
            "space": self.space,
            "events": self.events,
            "conjunction_types": self.conjunction_types,
            "max_distances": self.distance,
            "epoch_search_precision": self.epoch_search_precision if self.epoch_search_precision in [30, 60] else 60,
        }
        return self._query

    @query.setter
    def query(self, query: Dict) -> None:
        self._query = query

    def execute(self) -> None:
        """
        Initiate a conjunction search request

        Raises:
            pyaurorax.exceptions.AuroraXBadParametersException: too many criteria blocks
        """
        # check number of criteria blocks
        self.check_criteria_block_count_validity()

        # do request
        url = urls.conjunction_search_url
        req = AuroraXRequest(method="post",
                             url=url,
                             body=self.query,
                             null_response=True)
        res = req.execute()

        # set request ID, request_url, executed
        self.executed = True
        if res.status_code == 202:
            # request successfully dispatched
            self.executed = True
            self.request_url = res.request.headers["location"]
            self.request_id = self.request_url.rsplit("/", 1)[-1]

        # set request variable
        self.request = res

    def update_status(self, status: Optional[Dict] = None) -> None:
        """
        Update the status of this conjunction search request

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
            self.data_url = f'{urls.base_url}{status["search_result"]["data_uri"]}'

        # set class variable "status" and "logs"
        self.status = status
        self.logs = status["logs"]

    def check_for_data(self) -> bool:
        """
        Check to see if data is available for this conjunction
        search request

        Returns:
            True if data is available, else False
        """
        self.update_status()
        return self.completed

    def get_data(self) -> None:
        """
        Retrieve the data available for this conjunction search request
        """
        # check if request is completed
        if (self.completed is False):
            print("No data available, update status or check for data first")
            return

        # get data
        raw_data = requests_get_data(self.data_url, response_format=self.response_format)

        # set data variable
        if (self.response_format is not None):
            self.data = raw_data
        else:
            # cast data source objects
            for i in range(0, len(raw_data)):
                for j in range(0, len(raw_data[i]["data_sources"])):
                    ds = DataSource(**raw_data[i]["data_sources"][j], format=FORMAT_BASIC_INFO)
                    raw_data[i]["data_sources"][j] = ds

            # cast conjunctions
            self.data = [Conjunction(**c) for c in raw_data]

    def wait(self,
             poll_interval: Optional[float] = STANDARD_POLLING_SLEEP_TIME,
             verbose: Optional[bool] = False) -> None:
        """
        Block and wait until the request is complete and data is
        available for retrieval

        Args:
            poll_interval: time in seconds to wait between polling attempts, defaults
                to pyaurorax.requests.STANDARD_POLLING_SLEEP_TIME
            verbose: output poll times and other progress messages, defaults to False
        """
        url = urls.conjunction_request_url.format(self.request_id)
        self.update_status(requests_wait_for_data(url,
                                                  poll_interval=poll_interval,
                                                  verbose=verbose))

    def cancel(self,
               wait: Optional[bool] = False,
               poll_interval: Optional[float] = STANDARD_POLLING_SLEEP_TIME,
               verbose: Optional[bool] = False) -> int:
        """
        Cancel the conjunction search request

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
        url = urls.conjunction_request_url.format(self.request_id)
        return requests_cancel(url, wait=wait, poll_interval=poll_interval, verbose=verbose)
