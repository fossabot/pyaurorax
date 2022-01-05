import pyaurorax
import datetime
import time
from typing import Dict, List, Optional

# pdoc init
__pdoc__: Dict = {}

# globals
FIRST_FOLLOWUP_SLEEP_TIME = 0.050  # 50ms
STANDARD_POLLING_SLEEP_TIME = 1.0  # 1s


def get_status(request_url: str) -> Dict:
    """
    Retrieve the status of a request

    Args:
        request_url: the URL of the request information

    Returns:
        the status information for the request
    """
    # do request
    req = pyaurorax.AuroraXRequest(method="get", url=request_url)
    res = req.execute()

    # return
    return res.data


def get_data(data_url: str,
             post_body: Optional[Dict] = None) -> List:
    """
    Retrieve the data for a request. Makes a GET request if
    no post_body is specified, else makes a POST request with
    the given post_body.

    Args:
        data_url: the URL for the data of a request
        post_body: dictionary for body of a post request

    Returns:
        the list of JSON data objects in the response
    """
    # do request
    if post_body is not None:
        req = pyaurorax.AuroraXRequest(method="post",
                                       url=data_url,
                                       body=post_body)
    else:
        req = pyaurorax.AuroraXRequest(method="get", url=data_url)
    res = req.execute()

    # set data var
    data_result = res.data["result"]

    # serialize epochs and locations into datetimes and Locations
    for i in range(0, len(data_result)):
        if ("epoch" in data_result[i]):
            data_result[i]["epoch"] = datetime.datetime.strptime(data_result[i]["epoch"],
                                                                 "%Y-%m-%dT%H:%M:%S")
        if ("location_geo" in data_result[i]):
            data_result[i]["location_geo"] = pyaurorax.Location(lat=data_result[i]["location_geo"]["lat"],
                                                                lon=data_result[i]["location_geo"]["lon"])
        if ("location_gsm" in data_result[i]):
            data_result[i]["location_gsm"] = pyaurorax.Location(lat=data_result[i]["location_gsm"]["lat"],
                                                                lon=data_result[i]["location_gsm"]["lon"])
        if ("nbtrace" in data_result[i]):
            data_result[i]["nbtrace"] = pyaurorax.Location(lat=data_result[i]["nbtrace"]["lat"],
                                                           lon=data_result[i]["nbtrace"]["lon"])
        if ("sbtrace" in data_result[i]):
            data_result[i]["sbtrace"] = pyaurorax.Location(lat=data_result[i]["sbtrace"]["lat"],
                                                           lon=data_result[i]["sbtrace"]["lon"])

    # return
    return data_result


def get_logs(request_url: str) -> List:
    """
    Retrieve the logs for a request

    Args:
        request_url: the URL of the request information

    Returns:
        the list of logged messages for the request
    """
    # get status
    status = get_status(request_url)

    # return
    if ("logs" in status):
        return status["logs"]
    else:
        return []


def wait_for_data(request_url: str,
                  poll_interval: Optional[float] = STANDARD_POLLING_SLEEP_TIME,
                  verbose: Optional[bool] = False) -> Dict:
    """
    Block and wait for the data to be made available for a request

    Args:
        request_url: the URL of the request information
        poll_interval: seconds to wait between polling calls, defaults
            to STANDARD_POLLING_SLEEP_TIME
        verbose: output poll times, defaults to False

    Returns:
        the status information for the request
    """
    # get status
    status = get_status(request_url)

    # wait until request is done
    while (status["search_result"]["data_uri"] is None):
        time.sleep(poll_interval)
        if (verbose is True):
            print("[%s] Checking for data ..." % (datetime.datetime.now()))
        status = get_status(request_url)

    # return
    if (verbose is True):
        print("[%s] Data is now available" % (datetime.datetime.now()))
    return status


def cancel(request_url: str,
           wait: Optional[bool] = False,
           poll_interval: Optional[float] = STANDARD_POLLING_SLEEP_TIME,
           verbose: Optional[bool] = False) -> int:
    """
    Cancel the request at the given URL. This operation is asynchronous
    by default unless the wait param is set to True.

    Args:
        request_url: the URL string of the request to be canceled
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
    # do request
    req = pyaurorax.AuroraXRequest(method="delete",
                                   url=request_url,
                                   null_response=True)
    req.execute()

    # return immediately if we don't want to wait
    if (wait is False):
        return 1

    # get status
    status = get_status(request_url)

    # wait for request to be cancelled
    while (status["search_result"]["data_uri"] is None and status["search_result"]["error_condition"] is False):
        time.sleep(poll_interval)
        if (verbose is True):
            print("[%s] Checking for cancellation status ..." % (datetime.datetime.now()))
        status = get_status(request_url)

    # return
    if (verbose is True):
        print("[%s] The request has been cancelled" % (datetime.datetime.now()))
    return 1
