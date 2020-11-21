"""A OpenAPIProvider Service Provider."""

from masonite.provider import ServiceProvider
from app.commands.GenerateCommand import GenerateCommand


class OpenAPIProvider(ServiceProvider):
    """Provides Services To The Service Container."""

    wsgi = False

    def register(self):
        """Register objects into the Service Container."""
        self.app.bind("Generate", GenerateCommand())

    def boot(self):
        """Boots services required by the container."""
        pass
