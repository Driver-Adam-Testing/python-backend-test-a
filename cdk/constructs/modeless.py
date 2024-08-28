from constructs import Construct


class ModelessParams:
    environment: str

    def __init__(self, environment):
        self.environment = environment


class Modeless(Construct):
    def __init__(self, scope: Construct, id: str, params: ModelessParams):
        super().__init__(scope, id)
