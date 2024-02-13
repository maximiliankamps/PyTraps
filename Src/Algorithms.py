from Util import *


class OneshotSmart:
    """
    Oneshot is an on the fly algorithm that verifies for a Regular Transition Systems if it satisfies a property.
    (for more information on dodo please refer to my thesis)

    The class contains different implementations of Oneshot
    """

    def __init__(self, IxB, T):
        self.ignore_ambiguous = False
        self.IxB = IxB  # A pairing transducer from the NFA I and NFA B
        self.T = T  # The transition transducer T
        self.alphabet_map = T.get_alphabet_map()  # The alphabet map of the regular transition system
        self.step_cache = self.StepGameCache()
        self.expl_states = 0  # keeps count of the number of explored states
        self.expl_transitions = 0  # keeps count of the number of explored transitions 

    class StepGameCache:
        """
        Caches previously played step games
        (For more information please refer to my thesis)
        """

        def __init__(self):
            self.cache = {}
            self.cache_hits = 0  # keep track of the number of cache_hits during exploration

        def add_entry(self, c, gs, v, d_current, d_winning):
            self.cache[(tuple(c), gs.get_l(), gs.get_I(), v, tuple(d_current))] = d_winning

        def get_entry(self, c, gs, v, d_current):
            look_up = self.cache.get((tuple(c), gs.get_l(), gs.get_I(), v, tuple(d_current)))
            if look_up is not None:
                self.cache_hits += 1
            return look_up

        def print(self):
            for key in self.cache:
                print(f'{key} -> {self.cache[key]}')

    def min_sigma_disprove_oneshot(self, gen_func):
        """
        Restrict the alphabet of T by the partial target alphabets of I and B.
        Oneshot result is only valid when the algorithm disproves the property!
        (For more information refer to my thesis)
        :param gen_func: the generator function implementation for the construction of the seperator transducer
        :return: False if property was disproved
        """
        self.T = self.T.copy_with_restricted_trans(self.IxB.partial_sigma_origin, self.IxB.partial_sigma_target)
        value = self.oneshot_dfs(gen_func)
        if not value:
            print("Property could not be established!")
        return value

    def oneshot_dfs(self, gen_func):
        """
        Explore the intersection transducer in a dfs
        :param gen_func: the generator function implementation for the construction of the seperator transducer
        :return: A final state in the intersection or none
        """
        (ib0, c0) = (self.IxB.get_initial_states()[0], [self.T.get_initial_states()[0]])
        visited_states = {(ib0, tuple(c0))}
        for a in self.oneshot_dfs_helper(ib0, c0, visited_states, gen_func):
            return a
        return None

    def oneshot_dfs_helper(self, ib, c, visited_states, gen_func):
        """
        A helper function for one_shot_dfs
        :param ib: a state from the transducer IxB
        :param c: a state from the inductive transducer
        :param visited_states: a list of the already visited staes ib ∩ c
        :param gen_func: the generator function implementation for the construction of the seperator transducer
        :return:  A final state in the intersection transducer or none
        """
        # iterate over all transitions of the state ixb
        for (ib_trans, ib_succ) in self.IxB.get_transitions(ib):
            u, v = self.alphabet_map.get_y(ib_trans), self.alphabet_map.get_x(ib_trans)
            gs = Triple(0, refine_seperator(self.alphabet_map.get_bit_map_sigma(), u), 0)

            # iterate over all reachable (ib ∩ c) -> (ib_successor ∩ d)
            for d in gen_func(self, c, [], v, gs, []):
                self.expl_transitions += 1
                if (ib_succ, tuple(d)) not in visited_states:
                    visited_states.add((ib_succ, tuple(d)))
                    self.expl_states += 1
                    if self.IxB.is_final_state(ib_succ) and len(
                            list((filter(lambda q: (not self.T.is_final_state(q)), d)))) == 0:
                        yield ib_succ, d
                    yield from self.oneshot_dfs_helper(ib_succ, d, visited_states, gen_func)

    def oneshot_bfs(self, gen_func):
        """
        Explore the intersection transducer in a bfs
        :param gen_func: the generator function implementation for the construction of the seperator transducer
        :return: A final state in the intersection transducer or none
        """
        # Pairing of the initial states of (ixb ∩ reduced seperator transducer)
        (ib0, c0) = (self.IxB.get_initial_states()[0], [self.T.get_initial_states()[0]])
        work_set = [(ib0, c0)]
        visited_states = {(ib0, tuple(c0))}

        while len(work_set) != 0:
            (ib, c) = work_set.pop(0)

            # iterate over all transitions of the state ixb
            for (ib_trans, ib_succ) in self.IxB.get_transitions(ib):

                u, v = self.alphabet_map.get_y(ib_trans), self.alphabet_map.get_x(ib_trans)
                gs = Triple(0, refine_seperator(self.alphabet_map.get_bit_map_sigma(), u), 0)

                # iterate over all reachable (ib ∩ c) -> (ib_successor ∩ d)
                for d in gen_func(self, c, [], v, gs, []):
                    self.expl_transitions += 1
                    if (ib_succ, tuple(d)) not in visited_states:
                        visited_states.add((ib_succ, tuple(d)))
                        work_set.append((ib_succ, d))
                        self.expl_states += 1
                        if self.IxB.is_final_state(ib_succ) and len(
                                list((filter(lambda q: (not self.T.is_final_state(q)), d)))) == 0:
                            return ib_succ, d
        return None

    def step_game_gen_buffered_bfs(self, c1, c2, v, gs, visited):
        """
        This function lazily constructs states of the inductive transducer G_trap in a bfs.
        (For more information refer to my thesis)
        :param c1: List of the from-column
        :param c2: List of the to-column
        :param v: The symbol to be removed from the seperator
        :param gs: The game state <l, I, c_d>
        :param visited: A list keeping track of all winning states d
        :return: Lazily return states d of the inductive transducer
        Uses the same cache as the one_shot implementation of dodo, returns states d in a bfs
        """
        next_marked = []  # store if the next step gs_, c_ has been explored already
        if c2 in visited:  # Return if c2 has been visited
            return
        cache_hit = self.step_cache.get_entry(c1, gs, v, c2)  # Check if this partially played game is in cache
        if cache_hit is not None:
            for hit in cache_hit:
                yield hit
            return

        if len(c1) == gs.get_l() and symbol_not_in_seperator(gs.get_I(), v):  # Return c2 if step game is won
            visited.append(c2)
            yield c2

        candidates = []
        for (q, trans_gen) in map(lambda origin: (origin, self.T.get_transitions(origin)), c1[:gs.get_l() + 1]):
            for (qp_t, p) in trans_gen:
                x, y = self.alphabet_map.get_x(qp_t), self.alphabet_map.get_y(qp_t)
                if symbol_not_in_seperator(gs.get_I(), y):
                    if p not in c2:
                        c2_ = c2 + [p]
                        if c2_ in visited:
                            continue
                    else:
                        c2_ = c2
                    gs_ = Triple(gs.get_l() + (1, 0)[q in c1[:gs.get_l()]], refine_seperator(gs.get_I(), x),
                                 gs.get_d_p() + (1, 0)[p in c2])
                    if not gs.equal(gs_) and (gs_.get_l(), gs.get_I(), c2_) not in next_marked:
                        if self.ignore_ambiguous:
                            next_marked.append((gs_.get_l(), gs.get_I(), c2_))
                        candidates.append((c2_, gs_))
        for (c2_, gs_) in candidates:
            yield from self.step_game_gen_buffered_bfs(c1, c2_, v, gs_, visited)
        self.step_cache.add_entry(c1, gs, v, c2, visited)  # Add Game to cache

    def step_game_gen_simple_dfs(self, c1, c2, v, gs, visited):
        """Executes step_game_gen_dfs_helper without the use of the cache"""
        yield from self.step_game_gen_dfs_helper(c1, c2, v, gs, visited, False)

    def step_game_gen_cached_dfs(self, c1, c2, v, gs, visited):
        """Executes step_game_gen_dfs_helper with the use of the cache"""
        yield from self.step_game_gen_dfs_helper(c1, c2, v, gs, visited, True)

    def step_game_gen_dfs_helper(self, c1, c2, v, gs, visited, use_cache):
        """
        This function lazily constructs states of the inductive transducer G_trap in a dfs.
        (For more information refer to my thesis)
        :param use_cache: if true the cache is used
        :param c1: List of the from-column
        :param c2: List of the to-column
        :param v: The symbol to be removed from the seperator
        :param gs: The game state <l, I, c_d>
        :param visited: A list keeping track of all winning states d
        :return: Lazily return states d of the inductive transducer
        Uses the same cache as the one_shot implementation of dodo, returns states d in a dfs
        """
        next_marked = []  # used to exclude ambitious step games from consideration
        if c2 in visited:  # Return if c2 has been visited
            return
        if use_cache:
            cache_hit = self.step_cache.get_entry(c1, gs, v, c2)  # Check if this partially played game is in cache
            if cache_hit is not None:
                for hit in cache_hit:
                    yield hit
                return

        if len(c1) == gs.get_l() and symbol_not_in_seperator(gs.get_I(), v):  # Return c2 if step game is won
            visited.append(c2)
            yield c2

        # Try to make progress in the step game
        for (q, trans_gen) in map(lambda origin: (origin, self.T.get_transitions(origin)), c1[:gs.get_l() + 1]):
            for (qp_t, p) in trans_gen:
                x, y = self.alphabet_map.get_x(qp_t), self.alphabet_map.get_y(qp_t)
                if symbol_not_in_seperator(gs.get_I(), y):
                    if p not in c2:
                        c2_ = c2 + [p]
                        if c2_ in visited:
                            continue
                    else:
                        c2_ = c2
                    gs_ = Triple(gs.get_l() + (1, 0)[q in c1[:gs.get_l()]], refine_seperator(gs.get_I(), x),
                                 gs.get_d_p() + (1, 0)[p in c2])
                    if not gs.equal(gs_) and (gs_.get_l(), gs.get_I(), c2_) not in next_marked:
                        if self.ignore_ambiguous:
                            next_marked.append((gs_.get_l(), gs.get_I(), c2_))
                        yield from self.step_game_gen_dfs_helper(c1, c2_, v, gs_, visited, use_cache)
        self.step_cache.add_entry(c1, gs, v, c2, visited)  # Add played game to cache

    def print_oneshot_result(self, result_bool):
        """
        Print statistics after the execution of oneshot
        :param result_bool: determines if the property was proved or disproved
        """
        print("# states: " + str(self.expl_states))
        print("# cache hits: " + str(self.step_cache.cache_hits))
        print("# transitions: " + str(self.expl_transitions))
        if result_bool is None:
            print("Result: ✓")
        else:
            print("Result: x")
