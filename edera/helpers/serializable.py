import binascii

import six.moves.cPickle as pickle


class Serializable(object):
    """
    An object that can be serialized to an ASCII string and deserialized back.

    Should be pickling-friendly.
    """

    @classmethod
    def deserialize(cls, serialization):
        """
        Deserialize an object.

        Args:
            serialization (String)

        Returns:
            $cls - the deserialized object
        """
        return pickle.loads(binascii.unhexlify(serialization))

    def serialize(self):
        """
        Serialize the object.

        Returns:
            String
        """
        return binascii.hexlify(pickle.dumps(self, protocol=2)).decode("ASCII")
