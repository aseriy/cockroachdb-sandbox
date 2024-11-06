import random
import psycopg
import logging


class Stations:
    def __init__(
        self,
        seed: float = 0.0,
        my_arg: map = {},
        null_pct: float = 0,
        array: int = 0,
    ):
        self.array = array
        self.null_pct = null_pct
        self.rng: random.Random = random.Random(seed)
        self.my_arg = my_arg

        self.db_conn()

        self.stations = self.get_stations()



    def __del__(self):
        if self.connection is not None:
            self.connection.close()


    def __next__(self):
        retval = None

        if self.null_pct and self.rng.random() < self.null_pct:
            retval = ""
        else:
            retval = f"{self.rng.choice(self.stations)}"

        return retval



    def db_conn(self):
        self.connection = None

        try:
            self.connection = psycopg.Connection.connect(
                    self.my_arg['url'],
                    autocommit = True,
                    application_name = "dbworkload"
                )
        
        except Exception as e:
            logging.fatal("database connection failed")
            logging.fatal(e)
            exit()

        return self.connection

    

    def get_stations(self):
        stations = []

        with self.connection.cursor() as cur:
            cur.execute(
            "SELECT id FROM stations"
            )
            logging.debug("get_stations(): %s", cur.statusmessage)
            rows = cur.fetchall()
        
        for r in rows:
            stations.append(r[0])

        return stations
