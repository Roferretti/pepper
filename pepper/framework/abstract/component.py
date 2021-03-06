from pepper.framework.abstract import AbstractBackend
from pepper import logger

from logging import Logger
from typing import ClassVar


class ComponentDependencyError(Exception):
    """Raised when a Component Dependency hasn't been met"""
    pass


class AbstractComponent(object):
    """
    Abstract Base Component on which all Components are Based

    Parameters
    ----------
    backend: AbstractBackend
        Application :class:`~pepper.framework.abstract.backend.AbstractBackend`
    """

    def __init__(self, backend):
        # type: (AbstractBackend) -> None
        super(AbstractComponent, self).__init__()

        self._backend = backend
        self._log = logger.getChild(self.__class__.__name__)

    @property
    def log(self):
        # type: () -> Logger
        """
        Returns Component `Logger <https://docs.python.org/2/library/logging.html>`_

        Returns
        -------
        logger: logging.Logger
        """
        return self._log

    @property
    def backend(self):
        # type: () -> AbstractBackend
        """
        Application :class:`~pepper.framework.abstract.backend.AbstractBackend`

        Returns
        -------
        backend: AbstractBackend
        """
        return self._backend

    def require(self, cls, dependency):
        # type: (ClassVar[AbstractComponent], ClassVar[AbstractComponent]) -> AbstractComponent
        """
        Enforce Component Dependency by throwing an Exception when a dependency is missing

        Checks whether Dependency Component is present in the Method Resolution Order (mro)

        Parameters
        ----------
        cls: type
            Dependent: Component Type requiring dependency
        dependency: type
            Dependency: Component Type being dependency

        Returns
        -------
        dependency: AbstractComponent
            Requested Dependency
        """
        if not isinstance(self, dependency):
            raise ComponentDependencyError("{} depends on {}, which is not a superclass of {}".format(
                cls.__name__, dependency.__name__, self.__class__.__name__))

        if self.__class__.mro().index(cls) > self.__class__.mro().index(dependency):
            raise ComponentDependencyError("{0} depends on {1}, but {1} is not initialized before {0} in {2}".format(
                cls.__name__, dependency.__name__, self.__class__.__name__))

        return self
