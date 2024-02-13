"""Different helper functions for the one_shot implementations"""


class Triple:
    """Stores the game state <c_p, I, r> of the step game"""

    def __init__(self, l, I, d_p):
        """
        :param l: the current position in the origin column
        :param I: the seperator as a bit map
        :param d_p: the current target column as a list
        """
        self.l = l

        self.I = I
        self.d_p = d_p

    def get_I(self):
        return self.I

    def get_l(self):
        return self.l

    def get_d_p(self):
        return self.d_p

    def equal(self, triple):
        return self.l == triple.l and self.I == triple.I and self.d_p == triple.d_p

    def __str__(self):
        return "<" + str(self.l) + "," + bin(self.I) + "," + str(self.d_p) + ">"


"""Note, please refer to my thesis for an explanation of a Seperator"""


def symbol_not_in_seperator(I, i):
    """
    :param I: Seperator as a bit map
    :param i: an index of a symbol in I
    :return: true if the symbol with index i is in I
    """
    return (I & (1 << i)) == 0


def refine_seperator(I, i):
    """
    Remove the 1-bit at position i from I
    :param I: Seperator as a bit map
    :param i: an index of a symbol in I
    """
    return I & ~(1 << i)


def bit_map_seperator_to_inv_list(I, n):
    """
    :param I: Seperator as a bit map
    :param n: the length of the Separator I"
    :return:  the indices of all symbols that are not contained in I
    """
    inv_list = []
    for i in range(0, n):
        if I & (1 << i) == 0:
            inv_list.append(i)
    return inv_list


def optional_list(l):
    """
    :param l: a list
    :return: [] if the list is None else just l
    """
    if l is None:
        return []
    return l
