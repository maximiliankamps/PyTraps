import time
import signal
import Algorithms
import Automata

benchmarks = [
    ("Burns.json", ["nomutex"]),
    ("bakery.json", ["nomutex"]),
    ("MESI.json", ["modifiedmodified", "sharedmodified"]),
    ("MOESI.json", ["modifiedmodified", "exclusiveexclusive", "sharedexclusive", "ownedexclusive", "exclusivemodified",
                    "ownedmodified", "sharedmodified"]),
    ("synapse.json", ["dirtydirty", "dirtyvalid"]),
    ("dining-cryptographers.json", ["internal", "external"]),
    ("token-passing.json", ["manytoken", "notoken", "onetoken"]),
    ("voting-token-passing.json", ["initial", "gamewon", "notokennomarked"])
]

gen_implementations = {"buffer_bfs": Algorithms.OneshotSmart.step_game_gen_buffered_bfs,
                       "simple_dfs": Algorithms.OneshotSmart.step_game_gen_simple_dfs,
                       "buffer_dfs": Algorithms.OneshotSmart.step_game_gen_cached_dfs}
oneshot_implementations = {"multi_disprove",
                           "min_disprove",
                           "dfs",
                           "bfs"}

max_time = 20 * 60  # max time in seconds until execution of oneshot implementation is considered as timed out


class Timeout(Exception):
    pass


def try_one(o, oneshot_func, timeout_time, gen_imp):
    """
    This function tries to execute oneshot for the RTS captured in the object o. The execution times out
    after timeout_time with an error message
    :param o: A oneshot smart object
    :param oneshot_func: the oneshot implementation under test
    :param timeout_time: the time after which the one_shot func is considered as timed out
    :param gen_imp: the implementation for the generator function necessary for oneshot_func
    """

    def timeout_handler(signum, frame):
        raise Timeout()

    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_time)

    try:
        result = oneshot_func(gen_imp)
        o.print_oneshot_result(result)

    except Timeout:
        print('{} timed out after {} seconds'.format(oneshot_func.__name__, timeout_time))
        return None
    finally:
        signal.signal(signal.SIGALRM, old_handler)


def execute_benchmarks(benchmark_list, gen_name, oneshot_name, ignore_ambiguous):
    """
    Executes the benchmarks in benchmark_list for a oneshot implementation
    :param benchmark_list: list of bad NFA properties B
    :param gen_name: the name of the generator function
    :param oneshot_name: the name of the oneshot function
    :param ignore_ambiguous: bool for ignoring ambitious states in the step game
    :return:
    """
    gen_imp = gen_implementations.get(gen_name)
    oneshot_imp = oneshot_name in oneshot_implementations

    if gen_imp is None:
        print(f'Generator "{gen_name}" implementation does not exists!')
        return
    if oneshot_imp is False:
        print(f'Oneshot "{oneshot_name}" implementation does not exists!')
        return

    print(f'Using generator: "{gen_name}" and oneshot implementation "{oneshot_name}":')
    for benchmark_name, testcases in benchmark_list:
        print("================================================")
        print(benchmark_name)
        print("================================================")
        for test in testcases:
            print(test)
            rts = Automata.RTS(benchmark_name)
            t = rts.get_T()

            ixb = rts.get_IxB(test)

            start_time = time.time()

            o = Algorithms.OneshotSmart(ixb, t)
            o.ignore_ambiguous = ignore_ambiguous
            if oneshot_name == "multi_disprove":
                try_one(o, o.multi_disprove_oneshot, max_time, gen_imp)
            elif oneshot_name == "min_disprove":
                try_one(o, o.min_sigma_disprove_oneshot, max_time, gen_imp)
            elif oneshot_name == "dfs":
                try_one(o, o.oneshot_dfs, max_time, gen_imp)
            elif oneshot_name == "bfs":
                try_one(o, o.oneshot_bfs, max_time, gen_imp)

            end_time = time.time()

            print(f'elapsed_time: {end_time - start_time}')
            print("------------------------------------------------")


"""Run all benchmarks will all implementations"""
if __name__ == '__main__':
    execute_benchmarks(benchmarks, "buffer_bfs", "bfs", True)
    print("================================================")
    print("Ignore ambiguous == false")
    print("================================================")
    execute_benchmarks(benchmarks, "buffer_bfs", "bfs", False)
    print("================================================")
    execute_benchmarks(benchmarks, "buffer_bfs", "dfs", False)
    print("================================================")
    execute_benchmarks(benchmarks, "buffer_dfs", "bfs", False)
    print("================================================")
    execute_benchmarks(benchmarks, "buffer_dfs", "dfs", False)
    print("================================================")
    print("Ignore ambiguous == true")
    print("================================================")
    print("================================================")
    execute_benchmarks(benchmarks, "buffer_bfs", "dfs", True)
    print("================================================")
    execute_benchmarks(benchmarks, "buffer_dfs", "bfs", True)
    print("================================================")
    execute_benchmarks(benchmarks, "buffer_dfs", "dfs", True)
    print("================================================")
    print("Sigma disprove")
    print("================================================")
    execute_benchmarks(benchmarks, "buffer_bfs", "min_disprove", True)
    execute_benchmarks(benchmarks, "buffer_dfs", "min_disprove", True)
