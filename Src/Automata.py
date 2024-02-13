import Storage
import graphviz as gviz
from abc import ABC, abstractmethod
from itertools import *
import json
import re


def hash_state(column_list):
    """
    Used for the efficient representation of seperator transducer states 
    :param column_list: the column that is supposed to be hashed 
    :return: combines all states in column_list in to a string and returns the integer representation of that string
    """
    state_str = ""
    for state in column_list:
        state_str += str(state + 1)  # Important!!! + 1 to generate unique hash for columns with q0 states
    return int(state_str)


class AbstractTransducer(ABC):
    """Abstract storage type for transducers"""

    @abstractmethod
    def __init__(self, alphabet_map):
        pass

    @abstractmethod
    def add_final_state(self, state):
        """
        :param state: the final state 
        :return: add a final state to the transducer 
        """
        pass

    @abstractmethod
    def is_final_state(self, state):
        """
        :param state: a state 
        :return: whether, state a final state in the transducer 
        """
        pass

    @abstractmethod
    def get_final_states(self):
        """
        :return: the list of all final states 
        """
        pass

    @abstractmethod
    def get_alphabet_map(self):
        """
        :return: the alphabet map of the transducer 
        """
        pass

    @abstractmethod
    def add_transition(self, origin, x_y_int, target):
        """
        Stores a transition in the NFAStorage object capturing the transition relation of the transducer 
        :param origin: a transducer state
        :param x_y_int: a symbol from the alphabet sigma
        :param target: a transducer state
        """
        pass

    @abstractmethod
    def get_successors(self, origin, x_y_int):
        """
        :param origin: a transducer state
        :param x_y_int: a symbol from the alphabet sigma
        :return: all reachable successors for the origin via the x_y_int stored in in the NFAStorage object capturing
        the transition relation of the transducer
        """
        pass


class NFATransducer(AbstractTransducer):

    def __init__(self, alphabet_map):
        """
        :param alphabet_map: The alphabet map for the transducer
        """
        self.state_count = 0  # The number of states in the transducer
        self.initial_states = []  # A list of the initial states
        self.final_states = []  # A list of the final states
        self.alphabet_map = alphabet_map
        self.partial_sigma_origin = set()  # contains all actually used origin symbols
        self.partial_sigma_target = set()  # contains all actually used target symbols
        self.transitions = Storage.SimpleStorageNFA()  # captures the transition relation of the transducer

    def set_state_count(self, state_count):
        self.state_count = state_count

    def get_initial_states(self):
        return self.initial_states

    def add_initial_state(self, initial_state):
        self.initial_states.append(initial_state)

    def add_initial_state_list(self, initial_state_list):
        self.initial_states.extend(initial_state_list)

    def is_final_state(self, state):
        return state in self.final_states

    def add_final_state(self, state):
        if state not in self.final_states:
            self.final_states.append(state)

    def add_final_state_list(self, state_list):
        self.final_states.extend(state_list)

    def get_final_states(self):
        return self.final_states

    def get_alphabet_map(self):
        return self.alphabet_map

    def add_transition(self, origin, x_y_int, target):
        self.partial_sigma_origin.add(self.alphabet_map.get_x(x_y_int))
        self.partial_sigma_target.add(self.alphabet_map.get_y(x_y_int))
        self.transitions.add_transition(origin, x_y_int, target)

    def get_transitions(self, origin):
        yield from self.transitions.transition_iterator(origin)

    def get_successors(self, origin, x_y_int):
        return self.transitions.get_successors(origin, x_y_int)

    def state_iterator(self):
        return self.transitions.state_iterator()

    def copy_with_restricted_trans(self, origin_symbols, target_symbols):
        """
        Create a copy of the transducer and remove all transitions where:
        :param origin_symbols: x not in origin_symbols
        or
        :param target_symbols: y not in target_symbols
        :return: the resulting transducer
        => Used for the optimization of the restricted alphabet mode of oneshot. Please refer to my thesis for more
        information
        """
        copy = NFATransducer(self.alphabet_map)
        copy.initial_states = self.initial_states
        for q in self.state_iterator():
            for (x_y_int, p) in self.transitions.transition_iterator(q):
                if self.alphabet_map.get_x(x_y_int) in origin_symbols and self.alphabet_map.get_y(
                        x_y_int) in target_symbols:
                    copy.add_transition(q, x_y_int, p)
                    if p in self.final_states:
                        copy.add_final_state(p)
        return copy

    def to_dot(self, filename, column_hashing):
        """
        :param filename: the file name to store the dot representation in
        :param column_hashing: a mapping to the string representation of hashed states
        :return: a dot representation of the transducer
        """
        g = gviz.Digraph('G', filename="Pictures/" + f'{filename}')

        for source in self.state_iterator():
            for (x_y_int, target) in self.transitions.transition_iterator(source):
                x = self.alphabet_map.int_to_symbol(self.alphabet_map.get_x(x_y_int))
                y = self.alphabet_map.int_to_symbol(self.alphabet_map.get_y(x_y_int))
                if target is not None:
                    if column_hashing is not None:
                        g.node(column_hashing.get_column_str(source), column_hashing.get_column_str(source),
                               shape="circle")
                        g.edge(column_hashing.get_column_str(source),
                               column_hashing.get_column_str(target),
                               x + "\n" + y)
                    else:
                        g.node(str(source), str(source), shape="circle")
                        g.edge(str(source), str(target), x + "\n" + y)

        g.view()

    def nfa_to_dfa(self):
        """
        :return: Return a deterministic transducer from the non-deterministic transducer
        """
        result = NFATransducer(self.alphabet_map)
        work_queue = [self.initial_states.copy()]
        visited = [self.initial_states.copy()]
        result.initial_states = list(map(lambda x: hash_state([x]), self.initial_states.copy()))

        while len(work_queue) != 0:
            q_list = work_queue.pop(0)

            new_q = hash_state(q_list)
            if any(map(lambda x: x in self.final_states, q_list)):
                result.add_final_state(new_q)

            for t in self.alphabet_map.sigma_x_sigma_iterator():
                p_gen = filter(lambda x: x is not None, map(lambda q: self.get_successors(q, t), q_list))
                p_list = list(set(chain.from_iterable(p_gen)))
                if p_list:
                    new_p = hash_state(p_list)
                    if p_list not in visited:
                        work_queue.append(p_list)
                        visited.append(p_list)
                    result.add_transition(new_q, t, new_p)
        return result


def parse_transition_regex(regex, alph_map, id):
    """
    :param regex: The regex for transition from .json file
    :param alph_map: Maps string transitions symbols to bit encoding
    :param id: If set to true constructs id transducer transitions from NFA transition from .json file
    => Used to create transducers from the NFA I and NFA B to allow for their pairing
    (Refer to my thesis for an explanation on id transducers and NFA pairings)
    :return: A list of transducer transition [x,y] (in their int representation)
    """
    m = (map(lambda s: s[0] + "," + s[1],  # create a list of the product of sigma
             (product(alph_map.sigma, alph_map.sigma), zip(alph_map.sigma, alph_map.sigma))[id]))
    r = re.compile(((regex, f'{regex},{regex}')[id]))  # the pattern from the json file for transitions
    return list(map(lambda z: alph_map.combine_symbols(z[0], z[1]),  # map x y -> int (via the alphabet map)
                    (map(lambda y: y.split(","),  # remove the ','
                         filter(lambda x: r.match(x), m)))))  # match all x,y that satisfy the pattern r


def parse_transition_regex_dfa(trans_dict, alph_map):
    """
    => Returns a list of DFA transitions. Note that these are of the form (q, x, p) and
    not (q, [x,y], p) which are transducer transitions
    :param trans_dict: The specification of transition from .json file
    :param alph_map: Maps string transitions symbols to bit encoding
    :return: A list of transitions (q, x, p)
    """
    transitions = []
    for t in trans_dict:
        r = re.compile(t["letter"])
        q = int(t["origin"][1:])
        p = int(t["target"][1:])
        transitions.extend(
            list(map(lambda y: (q, alph_map.symbol_to_int(y), p), filter(lambda x: r.match(x), alph_map.sigma))))
    return transitions


class RTS:
    """
    A Regular transition system (RTS) is a triple <Sigma,T,I>. Sigma is an alphabet T is a transducer over that alphabet
    and I is a NFA.
    - I encodes the language of initial configurations.
    - T encodes transitions of the system.
    For more information on RTS refer to my thesis
    """
    def __init__(self, filename):
        """
        :param filename: File in which transducer is specified
        """
        self.IxB_dict = None  # Dictionary of all pairings of I and B
        self.B_dict = None  # dictionary of all bad word NFA's (refer to my thesis)
        self.I = None  # A transducer encoding the transitions of the system
        self.T = None  # A NFA encoding the initial configurations
        self.alphabet_map = None  # The alphabet_map for the RTS
        self.rts_from_json(filename)  # Initialize the RTS

    def get_I(self):
        return self.I

    def get_T(self):
        return self.T

    def get_B(self, property_name):
        return self.B_dict[property_name]

    def get_IxB(self, property_name):
        return self.IxB_dict[property_name]

    def rts_from_json(self, filename):
        """
        Initializes the RTS by:
        1.) creating the transducer T from the specification in filename.
        2.) creating the pairing of the NFA I and all property NFAs B
        resulting in a list of transducer IxB (with I and B specified in filename).
        :param filename: The file where the rts specifications are stored
        """
        file = open(f'benchmark/{filename}')
        rts_dict = json.load(file)
        alphabet_map = Storage.AlphabetMap(rts_dict["alphabet"])
        self.alphabet_map = alphabet_map

        initial_dict = rts_dict["initial"]
        transducer_dict = rts_dict["transducer"]
        properties_dict = rts_dict["properties"]

        self.T = self.build_transducer(transducer_dict, False)
        self.I = self.build_transducer(initial_dict, True)

        self.B_dict = {name: self.build_transducer(properties_dict[name], True) for name in
                       properties_dict}

        self.IxB_dict = {name: self.build_IxB_transducer(initial_dict, properties_dict[name]) for name in
                         properties_dict}

    def pair_transducers(self, q0, p0, t1, t2, f1, f2):
        """
        Pairs two NFAs A and B
        :param q0: the initial state of the first NFA A
        :param p0: the initial state of the second NFA B
        :param t1: the transition relation the first NFA A as a list
        :param t2: the transition relation the second NFA B as a list
        :param f1: list of final states of the first NFA A
        :param f2: list of final states of the second NFA B
        :return: the pairing AxB of the two NFAs
        """
        result = NFATransducer(self.alphabet_map)
        result.add_initial_state(hash_state([q0, p0]))

        Q = [(q0, p0)]
        W = []

        while len(Q) != 0:
            (q1, q2) = Q.pop(0)
            W.append((q1, q2))

            if q1 in f1 and q2 in f2:
                result.add_final_state(hash_state([q1, q2]))

            for (q1_, x, p1) in t1:
                for (q2_, y, p2) in t2:
                    if q1 == q1_ and q2 == q2_:
                        q1_q2_hash = hash_state([q1_, q2_])
                        p1p2hash = hash_state([p1, p2])
                        x_y_int = self.alphabet_map.combine_x_and_y(x, y)
                        if result.get_successors(q1_q2_hash, x_y_int) is None or p1p2hash not in result.get_successors(
                                q1_q2_hash, x_y_int):
                            result.add_transition(q1_q2_hash, x_y_int, p1p2hash)
                        if (p1, p2) not in W:
                            Q.append((p1, p2))
        return result

    def build_IxB_transducer(self, I_dict, B_dict):
        """
        Performs the pairing of two NFAs with the .json specification as input
        :param I_dict: transitions of the first NFA
        :param B_dict: transitions of the second NFA
        :return: the pairing transducer IxB
        """
        t1 = parse_transition_regex_dfa(I_dict["transitions"], self.alphabet_map)
        f1 = list(map(lambda q: int(q[1:]), I_dict["acceptingStates"]))

        t2 = parse_transition_regex_dfa(B_dict["transitions"], self.alphabet_map)
        f2 = list(map(lambda q: int(q[1:]), B_dict["acceptingStates"]))

        q0 = int(I_dict["initialState"][1:])
        p0 = int(B_dict["initialState"][1:])

        return self.pair_transducers(q0, p0, t1, t2, f1, f2)

    def built_id_transducer(self, nfa_dict):
        """
        :param nfa_dict: the specification of the transition relation of a NFA from the .json file
        :return: the id transducer resulting from the transition relation nfa_dict
        """
        id_transducer = NFATransducer(self.alphabet_map)
        id_transducer.add_initial_state(int(nfa_dict["initialState"][1:]))
        id_transducer.add_final_state_list(list(map(lambda q: int(q[1:]), nfa_dict["acceptingStates"])))
        for t in nfa_dict["transitions"]:
            letter = t["letter"]
            x_y_int = self.alphabet_map.combine_symbols(letter, letter)
            id_transducer.add_transition(int(t["origin"][1:]), x_y_int, int(t["target"][1:]))
        return id_transducer

    def build_transducer(self, trans_dict, id):
        """
        :param trans_dict: the transition specification of the transducer/NFA
        :param id: if_trans dict is a specification for an NFA and id is set to true, the function constructs an
        id transducer
        :return: a transducer
        """
        transducer = NFATransducer(self.alphabet_map)
        transducer.set_state_count(len(trans_dict["states"]))
        transducer.add_initial_state(int(trans_dict["initialState"][1:]))
        transducer.add_final_state_list(list(map(lambda q: int(q[1:]), trans_dict["acceptingStates"])))
        for t in trans_dict["transitions"]:
            for x_y_int in parse_transition_regex(t["letter"], self.alphabet_map, id):
                transducer.add_transition(int(t["origin"][1:]), x_y_int, int(t["target"][1:]))
        return transducer
