"""A IndexController Module."""

from masonite.request import Request
from masonite.view import View
from masonite.controllers import Controller
from app.Index import Index


class IndexController(Controller):
    """IndexController Controller Class."""

    def __init__(self, request: Request):
        """IndexController Initializer

        Arguments:
            request {masonite.request.Request} -- The Masonite Request class.
        """
        self.request = request
        self.model = Index

    def show(self, view: View):
        pass
