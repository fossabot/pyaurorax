import pyaurorax
import datetime
import pprint


def main():
    # set up params
    start = datetime.datetime(2020, 1, 1, 0, 0, 0)
    end = datetime.datetime(2020, 1, 1, 6, 59, 59)
    ground_params = [
        {"programs": ["themis-asi"]}
    ]
    space_params = [
        {"programs": ["swarm"]}
    ]
    distance = 200

    # create search object
    s = pyaurorax.conjunctions.search(start,
                                      end,
                                      ground=ground_params,
                                      space=space_params,
                                      distance=distance,
                                      return_immediately=True)

    # wait for data
    print("Waiting for request to complete ...")
    s.wait()

    # get data
    print("Get data ...")
    s.get_data()

    # print data
    print()
    pprint.pprint(s.data)


# ----------
if (__name__ == "__main__"):
    main()
