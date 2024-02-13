import math
from abc import ABC, abstractmethod
import itertools


class AbstractStorage(ABC):
    """abstract class for the storage of transducer transitions relations"""

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def add_transition(self, origin, symbol, target):
        """
        Stores a transition of (origin,symbol,target),
        in other words target is reachable from origin via symbol
        :param origin: a transducer state
        :param symbol: a symbol from the alphabet sigma
        :param target: a transducer state
        """
        pass

    @abstractmethod
    def get_successors(self, origin, symbol):
        """
        :param origin:
        :param symbol:
        :return: a list of target states reachable from origin via symbol
        """
        pass

    @abstractmethod
    def state_iterator(self):
        """
        :return: Returns an iterator over all states
        """
        pass

    @abstractmethod
    def __str__(self):
        pass


class SimpleStorageNFA(AbstractStorage):
    """Stores the transition relation of an NFA (Non-deterministic Finite Automaton) in a hashtable"""

    def __init__(self):
        self.state_count = 0
        self.dictionary = {}

    def add_transition(self, origin, symbol, target):
        self.state_count += 1
        if self.dictionary.get(origin) is None:
            self.dictionary[origin] = {symbol: [target]}
        elif self.dictionary.get(origin).get(symbol) is None:
            (self.dictionary[origin])[symbol] = [target]
        else:
            (self.dictionary[origin])[symbol].append(target)

    def get_successors(self, origin, symbol):
        look_up = self.dictionary.get(origin)
        if look_up is not None:
            return look_up.get(symbol)
        return None

    def state_iterator(self):
        return self.dictionary.keys()

    def transition_iterator(self, origin):
        if self.dictionary.get(origin) is None:
            return
        for s in self.dictionary[origin]:
            for target in self.dictionary[origin][s]:
                yield s, target

    def __str__(self):
        result = ""
        for state in self.dictionary:
            for symbol in self.dictionary[state]:
                result += "state: " + str(state) + " symbol: " + str(symbol) + " target: " + str(
                    (self.dictionary[state])[symbol]) + "\n"
        return result


class ColumnMapping:
    """
    Stores the string representation of hashed transducer states.
    Used for debugging purposes only"
    """

    def __init__(self, LSSF):
        """
        Depending on LSSF maps lists [0, 1, 2] to 012 or 210
        :param LSSF: Least significant state first (in this case would map to 012)
        """
        self.LSSF = LSSF
        self.mapping = {}

    def store_column(self, column_hash, column_list):
        """Maps [0, 1, 2] -> q0q1q2 and stores result in a map with key column_hash
        :param column_hash: the hash value of a column
        :param column_list: the list to be hashed
        """
        column_str = ""
        for entry in column_list:
            if self.LSSF:
                column_str = column_str + "q" + str(entry)
            else:
                column_str = "q" + str(entry) + column_str
        self.mapping[column_hash] = column_str

    def get_column_str(self, column_hash):
        """
        :param column_hash: the hash value of a column
        :return: returns the string representation of the column state encoded by column_hash
        """
        return self.mapping[column_hash]


class AlphabetMap:
    """
    Maps symbols from Sigma from string to int.
    Used to efficiently represent transducer transitions [x,y] (where x and y are symbols from sigma)
    and allows for bit manipulations.
    """

    def __init__(self, sigma):
        """:param sigma: a string list of symbols, e.g. [a,b,c]"""
        self.sigma = sigma
        # The number of bits necessary to encode all symbols in sigma, determines the size of bitmaps
        self.bits = int(math.ceil(math.log2(len(sigma))))
        # A mapping from the string representation of symbols to their integer representation
        self.symbolIntMap = self.init_map()

    def init_map(self):
        """initializes the map (example: a -> 0, b -> 1, c -> 2)"""
        tmp = {}
        for i, sym in enumerate(self.sigma):
            tmp[sym] = i
        return tmp

    def sigma_iterator(self):
        """:return an iterator over all symbols (in the integer representation)"""
        return range(0, self.get_sigma_size())

    def sigma_x_sigma_iterator(self):
        """:return an iterator over all pairings of symbols (in the integer representation)"""
        return map(lambda x_y: self.combine_x_and_y(x_y[0], x_y[1]),
                   itertools.product(self.sigma_iterator(), self.sigma_iterator()))

    def get_sigma_size(self):
        """:return the size of the alphabet sigma"""
        return len(self.sigma)

    def get_bit_map_sigma(self):
        """
        E.g. take sigma [1,2,3].
        The bitmap for the entire sigma would be 111 and for a subset like [1,3] the bitmap would be 101
        :return a bit map of the length of sigma
        """
        return (1 << len(self.sigma)) - 1

    def symbol_to_int(self, symbol):
        """
        :param symbol: a symbol from sigma in its string representation
        :return: a symbol to its integer representation
        """
        return self.symbolIntMap[symbol]

    def int_to_symbol(self, x):
        """
        :param x: a symbol from sigma in its int representation
        :return: a symbol to its string representation
        """
        return self.sigma[x]

    def combine_x_and_y(self, x_int, y_int):
        """
        :param x_int: a symbol in its int representation
        :param y_int: a symbol in its int representation
        :return: Combines int x and y in to [x,y], by concatenating the two integers.
        => Represents a transducer transition
        """
        return x_int << self.bits | y_int

    def combine_symbols(self, x_str, y_str):
        """
        Combines string x and y
        :param x_str: a symbol in its string representation
        :param y_str: a symbol in its string representation
        :return: Combines string x and y in to [x,y], by first mapping them to their int representation and
        then concatenating the two integers.
        => Represents a transducer transition
        """
        return self.combine_x_and_y(self.symbol_to_int(x_str), self.symbol_to_int(y_str))

    def get_x(self, x_y):
        """
        :param x_y: an integer representing a transducer transition [x,y]
        :return: x from [x,y]
        """
        return x_y >> self.bits

    def get_y(self, x_y):
        """
        :param x_y: an integer representing a transducer transition [x,y]
        :return: y from [x,y]
        """
        return x_y & (1 << self.bits) - 1

    def transition_to_str(self, x_y):
        """
        :param x_y: an integer representing a transducer transition [x,y]
        :return: a string of the transition [x,y]
        """
        return "[" + self.sigma[(self.get_x(x_y))] + "," + self.sigma[(self.get_y(x_y))] + "]"

    def __str__(self):
        tmp = ""
        for sym in self.symbolIntMap:
            tmp += str(sym) + "->" + bin(self.symbolIntMap[sym]) + "\n"
        return tmp
