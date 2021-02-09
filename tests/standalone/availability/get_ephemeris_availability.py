import aurorax
import datetime
import pprint


def main():
    # set parameters
    start_date = datetime.datetime(2019, 1, 1)
    end_date = datetime.date(2019, 1, 10)
    program = "swarm"
    platform = "swarma"
    instrument_type = "footprint"
    print("Retrieving ephemeris availability with the parameters:")
    print("  Start Date:\t\t%s" % (start_date.strftime("%Y-%m-%d")))
    print("  End Date:\t\t%s" % (end_date.strftime("%Y-%m-%d")))
    print("  Program:\t\t%s" % (program))
    print("  Platform:\t\t%s" % (platform))
    print("  Instrument Type:\t%s\n" % (instrument_type))

    # get availability
    availability = aurorax.availability.ephemeris(start_date,
                                                  end_date,
                                                  program=program,
                                                  platform=platform,
                                                  instrument_type=instrument_type)
    pprint.pprint(availability)


# ----------
if (__name__ == "__main__"):
    main()
