from pydantic import BaseModel


class ProcessedFileContent(BaseModel):
    content: str

    # def __init__(self, **data):
    #     super().__init__(**data)

    #     pp = pprint.PrettyPrinter(indent=4)
    #     pp.pprint(self.model_dump())
