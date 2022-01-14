import sys
import pprint
import click
import pyaurorax
from texttable import Texttable

# globals
SUPPORTED_SOURCE_TYPES = [
    pyaurorax.sources.SOURCE_TYPE_EVENT_LIST,
    pyaurorax.sources.SOURCE_TYPE_GROUND,
    pyaurorax.sources.SOURCE_TYPE_HEO,
    pyaurorax.sources.SOURCE_TYPE_LEO,
    pyaurorax.sources.SOURCE_TYPE_LUNAR,
]


@click.group("sources", help="Interact with data sources")
def sources_group():
    pass


@sources_group.command("list", short_help="List data sources")
@click.option("--program", type=str, help="Filter using program")
@click.option("--platform", type=str, help="Filter using platform")
@click.option("--instrument-type", type=str, help="Filter using instrument type")
@click.option("--source-type", type=click.Choice(SUPPORTED_SOURCE_TYPES),
              help="Filter using source type")
@click.option("--owner", type=str, help="Filter using an owner")
@click.option("--order", type=click.Choice(["identifier", "program", "platform",
                                            "instrument_type", "display_name",
                                            "owner"]),
              default="identifier", help="Order results using a certain column")
@click.option("--reversed", "reversed_", is_flag=True, help="Reverse ordering")
@click.pass_obj
def list(config, program, platform, instrument_type, source_type, owner, order, reversed_):
    """
    List data sources using the options to filter as desired
    """
    # get data sources
    try:
        sources = pyaurorax.sources.get_using_filters(program=program,
                                                      platform=platform,
                                                      instrument_type=instrument_type,
                                                      source_type=source_type,
                                                      owner=owner,
                                                      order=order)
    except pyaurorax.AuroraXException as e:
        click.echo("%s occurred: %s" % (type(e).__name__, e.args[0]))
        sys.exit(1)

    # reverse
    if (reversed_ is True):
        sources = reversed(sources)

    # decide if we want to show the owner
    show_owner = False
    if (owner is not None or order == "owner"):
        show_owner = True

    # set table lists
    table_identifiers = []
    table_programs = []
    table_platforms = []
    table_instrument_types = []
    table_source_types = []
    table_display_names = []
    table_owners = []
    for source in sources:
        table_identifiers.append(source.identifier)
        table_programs.append(source.program)
        table_platforms.append(source.platform)
        table_instrument_types.append(source.instrument_type)
        table_source_types.append(source.source_type)
        table_display_names.append(source.display_name)
        table_owners.append(source.owner)

    # set header values
    table_headers = ["Identifier", "Display Name", "Program",
                     "Platform", "Instrument Type", "Source Type"]
    if (show_owner is True):
        table_headers.append("Owner")
    for i in range(0, len(table_headers)):
        if (table_headers[i].lower().replace(' ', '_') == order):
            table_headers[i] += " " + "\u2193"

    # output information
    table = Texttable(max_width=400)
    table.set_deco(Texttable.HEADER)
    table.set_cols_dtype(["t"] * len(table_headers))
    table.set_header_align(["l"] * len(table_headers))
    table.set_cols_align(["l"] * len(table_headers))
    table.header(table_headers)
    for i in range(0, len(table_identifiers)):
        if (show_owner is True):
            table.add_row([table_identifiers[i],
                           table_display_names[i],
                           table_programs[i],
                           table_platforms[i],
                           table_instrument_types[i],
                           table_source_types[i],
                           table_owners[i]])
        else:
            table.add_row([table_identifiers[i],
                           table_display_names[i],
                           table_programs[i],
                           table_platforms[i],
                           table_instrument_types[i],
                           table_source_types[i]])
    click.echo(table.draw())


@sources_group.command("search", short_help="Search for data sources")
@click.option("--programs", type=str,
              help="Search for program (comma separate for multiple values)")
@click.option("--platforms", type=str,
              help="Search for platform (comma separate for multiple values)")
@click.option("--instrument-types", type=str,
              help="Search for instrument type (comma separate for multiple values)")
@click.option("--order", type=click.Choice(["identifier", "program", "platform",
                                            "instrument_type", "display_name",
                                            "owner"]),
              default="identifier", help="Order results using a certain column")
@click.option("--reversed", "reversed_", is_flag=True, help="Reverse ordering")
@click.pass_obj
def search(config, programs, platforms, instrument_types, order, reversed_):
    """
    Search for data sources using the options to filter as desired. Unlike
    the 'list' command filters, this command supports multiple programs,
    platforms, or instrument types (using commas).
    """
    # set programs values
    parsed_programs = []
    if (programs is None):
        pass
    elif (',' in programs):
        for p in programs.split(','):
            p = p.strip()
            if (len(p) > 0):
                parsed_programs.append(p)
    else:
        parsed_programs = [programs]

    # set platforms values
    parsed_platforms = []
    if (platforms is None):
        pass
    elif (',' in platforms):
        for p in platforms.split(','):
            p = p.strip()
            if (len(p) > 0):
                parsed_platforms.append(p)
    else:
        parsed_platforms = [platforms]

    # set instrument_types values
    parsed_instrument_types = []
    if (instrument_types is None):
        pass
    elif (',' in instrument_types):
        for p in instrument_types.split(','):
            p = p.strip()
            if (len(p) > 0):
                parsed_instrument_types.append(p)
    else:
        parsed_instrument_types = [instrument_types]

    # search for data sources
    try:
        sources = pyaurorax.sources.search(programs=parsed_programs,
                                           platforms=parsed_platforms,
                                           instrument_types=parsed_instrument_types,
                                           order=order)
    except pyaurorax.AuroraXException as e:
        click.echo("%s occurred: %s" % (type(e).__name__, e.args[0]))
        sys.exit(1)

    # reverse
    if (reversed_ is True):
        sources = reversed(sources)

    # decide if we want to show the owner
    show_owner = False
    if (order == "owner"):
        show_owner = True

    # set table lists
    table_identifiers = []
    table_programs = []
    table_platforms = []
    table_instrument_types = []
    table_source_types = []
    table_display_names = []
    table_owners = []
    for source in sources:
        table_identifiers.append(source.identifier)
        table_programs.append(source.program)
        table_platforms.append(source.platform)
        table_instrument_types.append(source.instrument_type)
        table_source_types.append(source.source_type)
        table_display_names.append(source.display_name)
        table_owners.append(source.owner)

    # set header values
    table_headers = ["Identifier", "Display Name", "Program",
                     "Platform", "Instrument Type", "Source Type"]
    if (show_owner is True):
        table_headers.append("Owner")
    for i in range(0, len(table_headers)):
        if (table_headers[i].lower().replace(' ', '_') == order):
            table_headers[i] += " " + "\u2193"

    # output information
    table = Texttable(max_width=400)
    table.set_deco(Texttable.HEADER)
    table.set_cols_dtype(["t"] * len(table_headers))
    table.set_header_align(["l"] * len(table_headers))
    table.set_cols_align(["l"] * len(table_headers))
    table.header(table_headers)
    for i in range(0, len(table_identifiers)):
        if (show_owner is True):
            table.add_row([table_identifiers[i],
                           table_display_names[i],
                           table_programs[i],
                           table_platforms[i],
                           table_instrument_types[i],
                           table_source_types[i],
                           table_owners[i]])
        else:
            table.add_row([table_identifiers[i],
                           table_display_names[i],
                           table_programs[i],
                           table_platforms[i],
                           table_instrument_types[i],
                           table_source_types[i]])
    click.echo(table.draw())


@sources_group.command("get", short_help="Get complete single data source record")
@click.argument("program", type=str)
@click.argument("platform", type=str)
@click.argument("instrument_type", type=str)
@click.pass_obj
def get(config, program, platform, instrument_type):
    """
    Get a complete `single data source record (full record format)

    \b
    PROGRAM             the program value
    PLATFORM            the platform value
    INSTRUMENT_TYPE     the instrument type value
    """
    # get data source
    try:
        ds = pyaurorax.sources.get(program=program,
                                   platform=platform,
                                   instrument_type=instrument_type)
        click.echo(pprint.pformat(ds.__dict__))
    except pyaurorax.AuroraXException as e:
        click.echo("%s occurred: %s" % (type(e).__name__, e.args[0]))
        sys.exit(1)


@sources_group.command("add", short_help="Add a data source")
@click.argument("program", type=str)
@click.argument("platform", type=str)
@click.argument("instrument_type", type=str)
@click.argument("source_type", type=click.Choice(SUPPORTED_SOURCE_TYPES))
@click.argument("display_name", type=str)
@click.option("--identifier", type=int, help="Custom identifier to use")
@click.pass_obj
def add(config, program, platform, instrument_type, source_type, display_name, identifier):
    """
    Add a data source

    \b
    PROGRAM             the program to set
    PLATFORM            the platform to set
    INSTRUMENT_TYPE     the instrument type to set
    SOURCE_TYPE         the source type to set
    DISPLAY_NAME        the display name to set
    """
    # add data source
    try:
        new_ds = pyaurorax.sources.DataSource(identifier=identifier,
                                              program=program,
                                              platform=platform,
                                              instrument_type=instrument_type,
                                              source_type=source_type,
                                              display_name=display_name)
        added_ds = pyaurorax.sources.add(new_ds)
        click.echo("Created data source successfully\n")
        click.echo(added_ds)
    except pyaurorax.AuroraXException as e:
        click.echo("%s occurred: %s" % (type(e).__name__, e.args[0]))
        sys.exit(1)


@sources_group.command("update", short_help="Update a data source")
@click.argument("identifier", type=str)
@click.option("--program", type=str, help="New program value")
@click.option("--platform", type=str, help="New platform value")
@click.option("--instrument-type", type=str, help="New instrument type value")
@click.option("--source-type", type=click.Choice(SUPPORTED_SOURCE_TYPES),
              help="New source type value")
@click.option("--display-name", type=str, help="New display name value")
@click.pass_obj
def update(config, identifier, program, platform, instrument_type, source_type, display_name):
    """
    Update a data source

    \b
    IDENTIFIER          the identifier of the data source to update
    """
    # get data sources
    try:
        ds = pyaurorax.sources.update_partial(identifier,
                                              program=program,
                                              platform=platform,
                                              instrument_type=instrument_type,
                                              source_type=source_type,
                                              display_name=display_name)
        click.echo("Updated data source successfully\n")
        click.echo(ds)
    except pyaurorax.AuroraXException as e:
        click.echo("%s occurred: %s" % (type(e).__name__, e.args[0]))
        sys.exit(1)


@sources_group.command("delete", short_help="Delete a data source")
@click.argument("identifier", type=int)
@click.pass_obj
def delete(config, identifier):
    """
    Delete a data source

    \b
    IDENTIFIER          the identifier of the data source to delete
    """
    # delete data source
    try:
        pyaurorax.sources.delete(identifier)
        click.echo("Successfully deleted data source #%d" % (identifier))
    except pyaurorax.AuroraXException as e:
        click.echo("%s occurred: %s" % (type(e).__name__, e.args[0]))
        sys.exit(1)
