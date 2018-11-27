import sys

from edera.helpers.boxes import MultiBox
from edera.helpers.proxy import Proxy


class Beanbag(object):
    """
    A module wrapper that replaces loaded submodules with "beans" they declare.

    The term "bean" refers to an environment-dependent (usually configurable) singleton object.
    Each submodule must declare a "Bean" class with an argumentless constructor that will be called.

    Examples:
        Let's create a simple bean in `my_package`:
            - in `my_package.beans.__init__` do

                >>> from edera.helpers import Beanbag
                >>> Beanbag(__name__)

            - in `my_package.beans.my_bean` do

                >>> class Bean(str):
                >>>     def __new__(cls):
                >>>         return "my_bean"

            - in other modules do

                >>> from my_package.beans import my_bean
                >>> my_bean
                'my_bean'

        You can import other beans to create your bean (avoid circular dependencies though):

            >>> from my_package.beans import my_other_bean
            >>> class Bean(str):
            >>>     def __new__(cls):
            >>>         return my_other_bean + "!"
    """

    def __delattr__(self, name):
        return delattr(object.__getattribute__(self, "___beanbag"), name)

    def __getattr__(self, name):
        return getattr(object.__getattribute__(self, "___beanbag"), name)

    def __init__(self, package_name):
        """
        Args:
            package_name (String) - the name of a package that will contain beans
        """
        object.__setattr__(self, "___beanbag", sys.modules[package_name])
        sys.modules[package_name] = self

    def __setattr__(self, name, value):
        object.__setattr__(self, name, getattr(value, "Bean")())


def split(*selectors):
    """
    Split bean instances by the values of the selectors.

    Will wrap the original bean class to create $MultiBox-based $Proxy's.

    Args:
        selectors (Tuple[Callable[[], Any]...])

    See also:
        $MultiBox
        $Proxy
    """

    def decorate(bean_class):

        class WrappedBean(bean_class):

            def __new__(cls):
                box = MultiBox(lambda: tuple(selector() for selector in selectors))
                return Proxy(box, bean_class)

        return WrappedBean

    return decorate
