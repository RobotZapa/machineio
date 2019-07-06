class Condition:
    def __init__(self):
        self.exp = []
        self.val_or_prev = []
        self.tol_or_bool = []
        self.change = []

    def add(self, read_expression, value, tolerance):
        '''
        Adds a new condition to be met to the condition
        :param read_expression: the code expression that yields the required value
        :param value: the value that is acceptable
        :param tolerance: the acceptable deviation + or - from the value
        :return:
        '''
        self.exp.append(read_expression)
        self.val_or_prev.append(value)
        self.tol_or_bool.append(tolerance)
        self.change.append(False)

    def add_changed(self, read_expression, boolean):
        '''
        Returns given boolean if the expression has changed since last check
        Returns the not of the boolean otherwise
        :param read_expression: the code expression that yields the required value
        :param boolean: True/False
        :return: True/False
        '''
        self.exp.append(read_expression)
        self.val_or_prev.append(None)
        self.tol_or_bool.append(boolean)
        self.change.append(True)

    def add_or(self, condition):
        pass
        #todo


    def __call__(self):
        '''
        Returns True or False
        :return:
        '''
        for i, expression in enumerate(self.exp):
            exp = eval(expression)
            if self.change[i] and self.val_or_prev[i] == exp and self.tol_or_bool[i] is False:
                return False
            if self.val_or_prev[i] + self.tol_or_bool[i] > exp > self.val_or_prev[i] - self.tol_or_bool[i]:
                pass
            else:
                return False
        return True
