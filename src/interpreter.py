##############################
#
# interpreter.py 
#
# Actual interpreter
#
# (C) 2016, Andreas Gaiser
##############################


import boxes

# (I) Arithmetic expressions
# 
# CONST
# VAR
# VAR (+) CONST
# VAR (+) VAR
#

# given as list-encoded trees.
# e.g.
# X + Y ==> ['+', X, Y]
#
# No nested expressions supported yet.


#
# (II) Assignments
#
# VAR := AExpr
#
# given as list expression:
# X := A + 1 ==> [':=', 'X', ['+', A, 1]]
#
#

#
# (III) Boolean expressions
#
# X (~) Y
# X (~) CONST
#
# given as list expression:
# ['<=', 'x', 'y']


class Method_CFG():

    def __init__(self, init_location, end_location):
        self.control_locs = [init_location, end_location]
        self.init_loc = init_location
        self.end_loc = end_location
        self.widen_points = []
        self.edges = {}

    def to_string(self):
        result = ''
        
        for (s, t) in self.edges:
            (cond, actions) = self.edges[(s, t)]
            result += '%s -> %s \n\t' % (s, t)
            if cond is None:
                result += ' [True] '
            else:
                result += ' %s ' % cond
            if len(actions) != 0:
                result += '\n\t'
                for action in actions:
                    result += ' @<%s> ' % action
            result += '\n'
            
        return result 
        
    def add_control_loc(self, control_loc, is_widen_point = False):
        self.control_locs.append(control_loc)
        if is_widen_point:
            self.widen_points.append(control_loc)

    def set_edge(self, loc1, loc2, condition, assignments):
        self.edges[(loc1, loc2)] = [condition, assignments]
        
    def forward_analyze(self,
                        dom,
                        head_init_element,
                        ordinary_init_element,
                        iterations_without_widening = 5):

        # evaluate an assignment
        # TODO: make this more extensible!
        def apply_assignment(assignment, value):
            (variable, expression) = assignment
            # case distinction:
            if len(expression) == 1:
                # constant or variable
                op1 = expression[0]
                return dom.op_binary(value,
                                     '+',
                                     variable,
                                     expression[0],
                                     0)
            elif len(expression) == 3:
                (operator, op1, op2) = expression
                return dom.op_binary(value,
                                     operator,
                                     variable,
                                     op1,
                                     op2)
                

        def apply_condition(condition, value):
            (operator, op1, op2) = condition
            return dom.cond_binary(value,
                                   operator,
                                   op1,
                                   op2)
                
        # init values
        values = {}
        for loc in self.control_locs:
            values[loc] = head_init_element if loc == self.init_loc else ordinary_init_element             
        def iterate(values, do_widen = True):
            new_values = {}
            for loc in values:
                new_values[loc] = values[loc]
            for loc in self.control_locs:
                buffer = values[loc]
                for (s, t) in self.edges:
                    if t == loc:
                        # print "EDGE: %s -> %s" %  (s, t)
                        (condition, assignments) = self.edges[(s, t)]
                        # is there a condition?
                        inflow = (apply_condition(condition, values[s])
                                  if (condition is not None) else values[s])
                        
                        for assignment in assignments:
                            inflow = apply_assignment(assignment, inflow)
                            
                        buffer = dom.union(buffer, inflow)
                new_values[loc] = buffer
            #print "PRE WIDEN:"
            #for loc in self.control_locs:
            #    print('"%s" : "%s"' % (loc, dom.to_string(new_values[loc])))
            if do_widen:
                for loc in self.widen_points:
                    new_values[loc] = dom.widen(values[loc], new_values[loc])
            postfixpoint_reached = True
            for loc in self.control_locs:
                # initialize results
                larger_or_equal = dom.is_subseteq(values[loc], new_values[loc])
                smaller_or_equal = dom.is_subseteq(new_values[loc], values[loc])
                is_increasing = larger_or_equal and not smaller_or_equal
                postfixpoint_reached = postfixpoint_reached and not is_increasing
            #print "POST WIDEN:"
            #for loc in self.control_locs:
            #    print('"%s" : "%s"' % (loc, dom.to_string(new_values[loc])))
            
            if postfixpoint_reached:
                for loc in self.control_locs:
                    print('"%s" : "%s"' % (loc, dom.to_string(new_values[loc])))

            return (postfixpoint_reached, new_values)

        postfixpoint_reached = False

        iterations = 0
        while not postfixpoint_reached:
            (postfixpoint_reached, values) \
                = iterate(values,
                          iterations > iterations_without_widening)
            iterations += 1
            
if __name__ == '__main__':

    boxes_factory = boxes.BoxDomainFactory(-128, 128)

    # example bounds001.c
    
    boxes_factory.add_var('index', -65536, 65536)
    boxes_factory.add_var('length', -65536, 65536)
    boxes_factory.add_var('access', -65536, 65536)

    def bounds_001():
    
        cfg = Method_CFG(1, 5)
        cfg.add_control_loc(2)
        cfg.add_control_loc(3)
        cfg.add_control_loc(4)
        
        cfg.set_edge(1, 2, None, [['length', [5]], ['access', [0]]])
        cfg.set_edge(2, 3,
                     ['>','index', 'length'],
                     [])
        cfg.set_edge(3, 5,
                     None,
                     [['access', [ '-', 'index', 'length']]])

        cfg.set_edge(2, 4,
                     ['<=','index', 'length'],
                     [])
        cfg.set_edge(4, 5,
                     None,
                     [['access', ['index']]])

        print cfg.to_string()

        cfg.forward_analyze(boxes_factory, boxes_factory.get_top(), boxes_factory.get_bot())


    def bounds_002():
    
        cfg = Method_CFG(1, 5)
        cfg.add_control_loc(2)
        cfg.add_control_loc(3)
        cfg.add_control_loc(4)
        
        cfg.set_edge(1, 2, None, [['length', [5]], ['access', [0]]])
        cfg.set_edge(2, 3,
                     ['>','index', 'length'],
                     [])
        cfg.set_edge(3, 5,
                     None,
                     [['access', [ '-', 'length', 1]]])

        cfg.set_edge(2, 4,
                     ['<=','index', 'length'],
                     [])
        cfg.set_edge(4, 5,
                     None,
                     [['access', ['index']]])

        print cfg.to_string()
        cfg.forward_analyze(boxes_factory, boxes_factory.get_top(), boxes_factory.get_bot())

        
    def bounds_003():
    
        cfg = Method_CFG(1, 6)
        cfg.add_control_loc(2)
        cfg.add_control_loc(3)
        cfg.add_control_loc(4)
        cfg.add_control_loc(5)
        
        cfg.set_edge(1, 2, None, [['length', [5]], ['access', [0]]])
        cfg.set_edge(2, 4,
                     ['>','index', 'length'],
                     [])
        cfg.set_edge(2, 3,
                     ['<=','index', 'length'],
                     [])
        cfg.set_edge(3, 4,
                     ['<','index', 0],
                     [])
        cfg.set_edge(3, 5,
                     ['>=','index', 0],
                     [])
        
        cfg.set_edge(4, 6,
                     None,
                     [['access', [ '-', 'length', 1]]])

        cfg.set_edge(5, 6,
                     None,
                     [['access', ['index']]])


        print cfg.to_string()
        cfg.forward_analyze(boxes_factory, boxes_factory.get_top(), boxes_factory.get_bot())


    def bounds_004():
    
        cfg = Method_CFG(1, 3)
        cfg.add_control_loc(2)
        
        cfg.set_edge(1, 2, None, [['length', [5]], ['access', [0]]])
        cfg.set_edge(2, 3,
                     None,
                     [['index', [ '%', 'index', 2]]])
        
        print cfg.to_string()
        cfg.forward_analyze(boxes_factory, boxes_factory.get_top(), boxes_factory.get_bot())

    print "BOUNDS 001"
    bounds_001()

    print "BOUNDS 002"
    bounds_002()

    print "BOUNDS 003"
    bounds_003()

    print "BOUNDS 004"
    bounds_004()
