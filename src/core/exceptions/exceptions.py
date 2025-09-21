class ExampleException(Exception):
    def __init__(self):
        self.message = 'Example exception'
        super().__init__(self.message)

class AlredyExistsException(Exception):
    def __init__(self):
        self.message = 'Already exists'
        super().__init__(self.message)