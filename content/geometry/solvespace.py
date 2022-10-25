import numpy as np
import cffi
from python_solvespace import SolverSystem as _SolverSystem
from functools import wraps

ffi = cffi.FFI()

ffi.cdef('''

typedef struct Slvs_Param{
    int h;
    int group;
    double val;
} Slvs_Param;

typedef struct Slvs_Entity{
    int h;
    int group;
    int type;
    int wrkpl;
    int point[4];
    int normal;
    int distance;
    int param[4];
} Slvs_Entity;

typedef struct Slvs_Constraint{
    int h;
    int group;
    int type;
    int wrkpl;
    double value;
    int ptA;
    int ptB;
    int entityA;
    int entityB;
    int entityC;
    int entityD;
    int other;
    int other2;
} Slvs_Constraint;

typedef struct system{
    size_t ref_count;
    size_t type;
    size_t vtab;
    int dof_v;
    int hGroup;
    Slvs_Param * param_begin;
    Slvs_Param * param_end;
    Slvs_Param * param_end_capacity;
    Slvs_Entity * entity_begin;
    Slvs_Entity * entity_end;
    Slvs_Entity * entity_end_capacity;
    Slvs_Constraint * constraint_begin;
    Slvs_Constraint * constraint_end;
    Slvs_Constraint * constraint_end_capacity;
} system;
''')


Constraints = ['coincident',
 'distance',
 'equal',
 'equal_angle',
 'equal_point_to_line',
 'ratio',
 'symmetric',
 'symmetric_h',
 'symmetric_v',
 'midpoint',
 'horizontal',
 'vertical',
 'diameter',
 'same_orientation',
 'angle',
 'perpendicular',
 'parallel',
 'tangent',
 'distance_proj',
 'dragged']        


class SolverSystem(_SolverSystem):
    def __init__(self):
        super().__init__()
        self.p = ffi.cast('system *', ffi.cast('void *', id(self)))
    
    @property
    def last_constraint_id(self):
        return (self.p.constraint_end - self.p.constraint_begin) - 1
    
    @property
    def constraints(self):
        return self.p.constraint_begin[0:self.p.constraint_end - self.p.constraint_begin]   
    
def wrap_constraint(name):
    cf = getattr(SolverSystem, name)
    
    @wraps(cf)
    def f(self, *args):
        cf(self, *args)
        return self.last_constraint_id
    
    return f
    
for name in Constraints:
    setattr(SolverSystem, name, wrap_constraint(name))