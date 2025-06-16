from TM1py import TM1Service
from .StarCellService import StarCellService
from .StarElementService import StarElementService

class StarTM1Service(TM1Service):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cells = StarCellService(self._tm1_rest)
        self.elements = StarElementService(self._tm1_rest)



