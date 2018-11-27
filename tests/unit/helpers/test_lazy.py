from edera.helpers import Lazy


def test_lazy_delays_instantiation_and_can_be_destroyed():

    class Object(object):

        def __init__(self, x):
            collector.append(x)

    collector = []
    lazy = Lazy[Object]("so lazy")
    assert not collector
    assert isinstance(lazy.instance, Object)
    assert collector == ["so lazy"]
    lazy.destroy()
    assert lazy.instance is not None
    assert collector == ["so lazy", "so lazy"]
