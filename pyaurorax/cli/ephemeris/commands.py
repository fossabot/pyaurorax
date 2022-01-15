import sys
import click
import pprint
import json
import pyaurorax
from dateutil.parser import parse
from ..helpers import (print_request_logs_table,
                       print_request_status,
                       get_search_data)
from ..templates import EPHEMERIS_SEARCH_TEMPLATE


@click.group("ephemeris", help="Interact with ephemeris searches")
def ephemeris_group():
    pass


@ephemeris_group.command("get_status",
                         short_help="Get status info for an ephemeris search request")
@click.argument("request_uuid", type=str)
@click.option("--show-logs", "show_logs", is_flag=True,
              help="Show the logs for the request")
@click.option("--show-query", "show_query", is_flag=True,
              help="Show the query for the request")
@click.option("--filter-logs",
              type=click.Choice(["debug", "info", "warn", "error"]),
              help="Filter log messages (used with --show-logs)")
@click.option("--table-max-width", "--max-width", type=int,
              help="Max width for the logs table")
@click.pass_obj
def get_status(config, request_uuid, show_logs, show_query, filter_logs, table_max_width):
    """
    Get information for an ephemeris search request

    \b
    REQUEST_UUID    the request unique identifier
    """
    # get request status
    try:
        url = pyaurorax.api.urls.ephemeris_request_url.format(request_uuid)
        s = pyaurorax.requests.get_status(url)
    except pyaurorax.AuroraXNotFoundException as e:
        click.echo("%s occurred: request ID not found" % (type(e).__name__))
        sys.exit(1)
    except pyaurorax.AuroraXException as e:
        click.echo("%s occurred: %s" % (type(e).__name__, e.args[0]))
        sys.exit(1)

    # print status nicely
    print_request_status(s,
                         show_logs=show_logs,
                         show_query=show_query,
                         filter_logs=filter_logs,
                         table_max_width=table_max_width)


@ephemeris_group.command("get_logs",
                         short_help="Get logs for an ephemeris search request")
@click.argument("request_uuid", type=str)
@click.option("--filter", "--filter-logs", "filter_",
              type=click.Choice(["debug", "info", "warn", "error"]),
              help="Filter log messages")
@click.option("--table-max-width", "--max-width", type=int,
              help="Max width for the logs table")
@click.pass_obj
def get_logs(config, request_uuid, filter_, table_max_width):
    """
    Get the logs for an ephemeris search request

    \b
    REQUEST_UUID    the request unique identifier
    """
    # get request status
    try:
        url = pyaurorax.api.urls.ephemeris_request_url.format(request_uuid)
        s = pyaurorax.requests.get_status(url)
    except pyaurorax.AuroraXNotFoundException as e:
        click.echo("%s occurred: request ID not found" % (type(e).__name__))
        sys.exit(1)
    except pyaurorax.AuroraXException as e:
        click.echo("%s occurred: %s" % (type(e).__name__, e.args[0]))
        sys.exit(1)

    # print out the logs nicely
    if ("logs" in s):
        print_request_logs_table(s["logs"],
                                 filter_level=filter_,
                                 table_max_width=table_max_width)
    else:
        click.echo("Search logs: missing, unable to display")


@ephemeris_group.command("get_query",
                         short_help="Get query for an ephemeris search request")
@click.argument("request_uuid", type=str)
@click.pass_obj
def get_query(config, request_uuid):
    """
    Get the query for an ephemeris search request

    \b
    REQUEST_UUID    the request unique identifier
    """
    # get request status
    try:
        url = pyaurorax.api.urls.ephemeris_request_url.format(request_uuid)
        s = pyaurorax.requests.get_status(url)
    except pyaurorax.AuroraXNotFoundException as e:
        click.echo("%s occurred: request ID not found" % (type(e).__name__))
        sys.exit(1)
    except pyaurorax.AuroraXException as e:
        click.echo("%s occurred: %s" % (type(e).__name__, e.args[0]))
        sys.exit(1)

    # print out query
    if ("query" in s["search_request"]):
        query_to_show = s["search_request"]["query"]
        del query_to_show["request_id"]
        click.echo(pprint.pformat(query_to_show))
    else:
        click.echo("\nSearch query missing from request status, unable to display")


@ephemeris_group.command("get_data",
                         short_help="Get data for an ephemeris search request")
@click.argument("request_uuid", type=str)
@click.option("--outfile", type=str, help="output file to save data to (a .json file)")
@click.option("--output-to-terminal", type=click.Choice(["dict", "objects"]),
              help="output data to terminal in a certain format (instead of to file)")
@click.option("--indent", type=int, default=2, show_default=True,
              help="indentation when saving data to file")
@click.option("--minify", is_flag=True, help="Minify the JSON data saved to file")
@click.pass_obj
def get_data(config, request_uuid, outfile, output_to_terminal, indent, minify):
    """
    Get the data for an ephemeris search request

    \b
    REQUEST_UUID    the request unique identifier
    """
    get_search_data("ephemeris",
                    request_uuid,
                    outfile,
                    output_to_terminal,
                    indent,
                    minify)


@ephemeris_group.command("search_resubmit",
                         short_help="Resubmit an ephemeris search request")
@click.argument("request_uuid", type=str)
@click.pass_obj
def search_resubmit(config, request_uuid):
    """
    Resubmit an ephemeris search request

    \b
    REQUEST_UUID    the request unique identifier
    """
    # get request status
    try:
        click.echo("Retrieving query for request '%s' ..." % (request_uuid))
        url = pyaurorax.api.urls.ephemeris_request_url.format(request_uuid)
        status = pyaurorax.requests.get_status(url)
    except pyaurorax.AuroraXNotFoundException as e:
        click.echo("%s occurred: request ID not found" % (type(e).__name__))
        sys.exit(1)
    except pyaurorax.AuroraXException as e:
        click.echo("%s occurred: %s" % (type(e).__name__, e.args[0]))
        sys.exit(1)

    # set the query to use for resubmission
    if ("query" not in status["search_request"]):
        click.echo("Error resubmitting: missing query from original request ID")
        sys.exit(1)
    q = status["search_request"]["query"]

    # create search object
    click.echo("Preparing new search ...")
    start = parse(q["start"], ignoretz=True)
    end = parse(q["end"], ignoretz=True)
    programs = None if "programs" not in q["data_sources"] else q["data_sources"]["programs"]
    platforms = None if "platforms" not in q["data_sources"] else q["data_sources"]["platforms"]
    instrument_types = None if "instrument_types" not in q["data_sources"] else q["data_sources"]["instrument_types"]
    metadata_filters = None
    metadata_filters_logical_operator = None
    if ("ephemeris_metadata_filters" in q["data_sources"]):
        if ("expressions" in q["data_sources"]["ephemeris_metadata_filters"]):
            metadata_filters = q["data_sources"]["ephemeris_metadata_filters"]["expressions"]
        if ("logical_operator" in q["data_sources"]["ephemeris_metadata_filters"]):
            metadata_filters_logical_operator = q["data_sources"]["ephemeris_metadata_filters"]["logical_operator"]
    s = pyaurorax.ephemeris.Search(start,
                                   end,
                                   programs=programs,
                                   platforms=platforms,
                                   instrument_types=instrument_types,
                                   metadata_filters=metadata_filters,
                                   metadata_filters_logical_operator=metadata_filters_logical_operator)

    # submit search
    click.echo("Submitting new search ...")
    s.execute()

    # output new request ID
    click.echo("Request has been resubmitted, new request ID is %s" % (s.request_id))


@ephemeris_group.command("search_template",
                         short_help="Output template for an ephemeris search request")
@click.option("--outfile", type=str, help="save template to a file")
@click.option("--indent", type=int, default=2, show_default=True,
              help="indentation to use when outputing template")
@click.pass_obj
def search_template(config, outfile, indent):
    """
    Output template for an ephemeris search request
    """
    if (outfile is not None):
        with open(outfile, 'w', encoding="utf-8") as fp:
            json.dump(EPHEMERIS_SEARCH_TEMPLATE, fp, indent=indent)
        click.echo("Saved template to %s" % (outfile))
    else:
        click.echo(json.dumps(EPHEMERIS_SEARCH_TEMPLATE, indent=indent))
