import csv
from typing import List, Literal
from abc import ABC, abstractmethod

import numpy as np

from mnms.demand.user import User
from mnms.tools.time import Time


class AbstractDemandManager(ABC):
    """Abstract class for loading a User demand
    """
    @abstractmethod
    def get_next_departures(self, tstart:Time, tend: Time) -> List[User]:
        """Return the Users with a departure time between tstart and tend

        Parameters
        ----------
        tstart: Time
            Lower bound of departure time
        tend: Time
            Upper bound of departure time

        Returns
        -------
        List[User]

        """
        pass


class BaseDemandManager(ABC):
    """Basic demand manager, it takes a list of User as input

    Parameters
    ----------
    users: List[User]
        list of User to manage
    """
    def __init__(self, users):
        self._users = users
        self._iter_demand = iter(self._users)
        self._current_user = next(self._iter_demand)

        self.nb_users = len(self._users)

    def get_next_departures(self, tstart:Time, tend:Time) -> List[User]:
        departure = list()
        while tstart <= self._current_user.departure_time < tend:
            departure.append(self._current_user)
            try:
                self._current_user = next(self._iter_demand)
            except StopIteration:
                return departure
        return departure

    def show_users(self):
        for u in self._users:
            print(u)


class CSVDemandManager(AbstractDemandManager):
    """Read a demand from a CSV file

    Parameters
    ----------
    csvfile: str
        Path to the CSV file
    demand_type: Literal[node, coordinate]
        Type of demand, either the origin?destination are node ids or coordinates
    delimiter: str
        Delimiter for the CSV file
    """
    def __init__(self, csvfile, demand_type:Literal['node', 'coordinate']='node', delimiter=';'):

        self._filename = csvfile
        self._file = open(self._filename, 'r')
        self._reader = csv.reader(self._file, delimiter=delimiter, quotechar='|')
        self._demand_type = demand_type

        next(self._reader)
        self._current_user = self.construct_user(next(self._reader))

    def get_next_departures(self, tstart:Time, tend:Time) -> List[User]:
        departure = list()
        while tstart <= self._current_user.departure_time < tend:
            departure.append(self._current_user)
            try:
                self._current_user = self.construct_user(next(self._reader))
            except StopIteration:
                return departure
        return departure

    def construct_user(self, row):
        if self._demand_type == 'node':
            user = User(row[0], row[2], row[3], Time(row[1]))
        elif self._demand_type == 'coordinate':
            user = User(row[0], np.fromstring(row[2], sep=' '), np.fromstring(row[3], sep=' '), Time(row[1]))
        else:
            raise TypeError(f"demand_type must be either 'node' or 'coordinate'")
        return user

    def __del__(self):
        self._file.close()