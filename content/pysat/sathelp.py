from itertools import combinations


def logic_expr_to_cnf_pattern(expr, symbol_list):
    from sympy import Not, to_cnf, Or

    def symbol_to_variable(s):
        if isinstance(s, Not):
            return -sym_map[s.args[0]]
        else:
            return sym_map[s]    
        
    expr = to_cnf(expr)
    variable_list = range(1, len(symbol_list) + 1)
    sym_map = {s:i for i, s in zip(variable_list, symbol_list)}
    
    res = []
    for arg in expr.args:
        if isinstance(arg, Or):
            term = [symbol_to_variable(s) for s in arg.args]
            res.append(term)
        else:
            res.append([symbol_to_variable(arg)])
    return res

def nbit_sequence(n):
    from sympy import Xor, And, Or, Not, symbols

    def half_adder(a, b):
        s = Xor(a, b)
        c = And(a, b)
        return s, c

    def full_adder(a, b, x):
        s1, c1 = half_adder(a, b)
        s2, c2 = half_adder(s1, x)
        return s2, Or(c1, c2)

    def nbit_adder(A, B):
        S = []
        for i, (a, b) in enumerate(zip(A, B)):
            if i == 0:
                s, c = half_adder(a, b)
            else:
                s, c = full_adder(a, b, c)
            S.append(s)
        return S       

    A = symbols(f'A:{n}')
    B = symbols(f'B:{n}')
    C = [0] * n
    C[0] = 1
    inc_expr = And(*[Not(Xor(b, s)) for b, s in zip(B, nbit_adder(A, C))])
    cnfs_pattern = logic_expr_to_cnf_pattern(inc_expr, A + B)
    return cnfs_pattern  


class SATHelper:
    def __init__(self):
        self.current = 1
        self.cnfs = []

    def __next__(self):
        v = self.current
        self.current += 1
        return v

    def not_(self, v):
        self.extend([[-v]])

    def next(self, n=0):
        if n == 0:
            return next(self)
        else:
            return self._get_variables(n)

    def _get_variables(self, n):
        n = int(n)
        variables = list(range(self.current, self.current + n))
        self.current += n
        return variables

    def exact_n(self, variables, n, extend=True):
        cnfs = []
        variables = [int(v) for v in variables]
        for c in combinations(variables, n + 1):
            cnfs.append([-v for v in c])

        for c in combinations(variables, len(variables) - n + 1):
            cnfs.append([v for v in c])

        if extend:
            self.extend(cnfs)

        return cnfs

    def atmost_one(self, variables, extend=True):
        variables = [int(v) for v in variables]
        cnfs = []
        for v1, v2 in combinations(variables, 2):
            cnfs.append([-v1, -v2])

        if extend:
            self.extend(cnfs)

        return cnfs

    def equals_to(self, variables, counts, extend=True):
        dnfs = []
        variables = [int(v) for v in variables]
        index = list(range(len(variables)))
        for c in counts:
            for plus_index in combinations(index, c):
                dnf = [-v for v in variables]
                for i in plus_index:
                    dnf[i] *= -1
                dnfs.append(dnf)
        return self.dnf_to_cnf(dnfs, extend=extend)

    def extend(self, cnfs):
        self.cnfs.extend(cnfs)

    def implies(self, A, B, extend=True):
        if isinstance(B, int):
            B = [B]
        cnf = [-A] + B

        if extend:
            self.extend([cnf])

        return cnf

    def implies_all(self, A, Bs, extend=True):
        cnfs = []
        for B in Bs:
            cnfs.append(self.implies(A, B, extend=extend))
        return cnfs        

    def dnf_to_cnf(self, dnf, extend=True):
        zlist = []
        cnfs = []
        for term in dnf:
            z = next(self)
            zlist.append(z)
            cnfs.append([z] + [-v for v in term])
            for v in term:
                cnfs.append([-z, v])
        cnfs.append(zlist)
        
        if extend:
            self.extend(cnfs)

        return cnfs

    def replace_cnf_pattern(self, cnf_pattern, variables, extend=True):
        def r(v):
            idx = abs(v) - 1
            if v < 0:
                return -variables[idx]
            else:
                return variables[idx]
        cnfs = [[r(v) for v in row] for row in cnf_pattern]

        if extend:        
            self.extend(cnfs)
        return cnfs

    def implies_pattern(self, v, cnf_pattern, variables, extend=True):
        cnfs = self.replace_cnf_pattern(cnf_pattern, variables, extend=False)
        return self.implies_all(v, cnfs, extend=extend)

    def solve(self):
        from pysat.solvers import Solver
        self.solver = solver = Solver()
        solver.append_formula(self.cnfs)
        ret = solver.solve()
        if ret is not None:
            return solver.get_model()