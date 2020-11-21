"""A SampleController Module."""

from masonite.request import Request
from masonite.view import View
from masonite.controllers import Controller
from app.Sample import Sample


class SampleController(Controller):
    """SampleController Controller Class."""

    tags = ["Cool", "Awesome", "Open-source"]

    def __init__(self, request: Request):
        """SampleController Initializer

        Arguments:
            request {masonite.request.Request} -- The Masonite Request class.
        """
        self.request = request
        self.model = Sample

    def one(self, view: View, request: Request) -> str:
        """
        Sample one controller
        """
        pass

    def many(self, view: View, request: Request) -> [str]:
        """
        Sample many controller
        """
        pass

    def create(self, view: View, request: Request) -> (str, int):
        """
        Sample create controller
        """
        pass
