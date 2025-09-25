class ExampleException(Exception):
    def __init__(self):
        self.message = 'Example exception'
        super().__init__(self.message)

class AlreadyExistsException(Exception):
    def __init__(self):
        self.message = 'Already exists'
        super().__init__(self.message)

class NotFoundException(Exception):
    def __init__(self):
        self.message = 'Not found'
        super().__init__(self.message)

class DatabaseException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)