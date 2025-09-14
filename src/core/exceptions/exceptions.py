class ExampleException(Exception):
    def __init__(self):
        self.message = 'Example exception'
        super().__init__(self.message)