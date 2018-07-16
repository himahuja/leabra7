"""A network."""
from typing import Dict
from typing import Iterable
from typing import List

from leabra7 import layer
from leabra7 import log
from leabra7 import program as prg  # renamed to avoid shadowing later
from leabra7 import projn
from leabra7 import specs


class Net(prg.EventListenerMixin):
    """A leabra7 network. This is the main class."""

    def __init__(self) -> None:
        # Each of the following dicts is keyed by the name of the object
        self.objs: Dict[str, prg.EventListenerMixin] = {}
        self.layers: Dict[str, layer.Layer] = {}
        self.projns: Dict[str, projn.Projn] = {}
        self.cycle_loggers: List[log.Logger] = []

    def _validate_obj_name(self, name: str) -> None:
        """Checks if a name exists within the objects dict.

        Args:
            name: The name to check.

        Raises:
            ValueError: If the name does not exist within the objects dict.
                This is not AssertionError because it is intended to be called
                within user-facing methods.

        """
        if name not in self.objs:
            raise ValueError("No object found with name {0}".format(name))

    def _get_layer(self, name: str) -> layer.Layer:
        """Gets a layer by name.

        Args:
            name: The name of the layer

        Raises:
            ValueError: If the name does not refer to a layer.
                This is not AssertionError because it is intended to be called
                within user-facing methods.

        """
        try:
            return self.layers[name]
        except KeyError:
            raise ValueError(
                "Name {0} does not refer to a layer.".format(name))

    def new_layer(self, name: str, size: int,
                  spec: specs.LayerSpec = None) -> None:
        """Adds a new layer to the network.

        Args:
            name: The name of the layer.
            size: How many units the layer should have.
            spec: The layer specification.

        Raises:
            spec.ValidationError: If the spec contains an invalid parameter
                value.

        """
        if spec is not None:
            spec.validate()
        lr = layer.Layer(name, size, spec)
        self.layers[name] = lr
        self.objs[name] = lr

        if lr.spec.log_on_cycle != ():
            self.cycle_loggers.append(log.Logger(lr, lr.spec.log_on_cycle))

    def force_layer(self, name: str, acts: Iterable[float]) -> None:
        """Forces the layer's activations.

        After forcing, the layer's activations will be set to the values
        contained in `acts` and will not change from cycle to cycle.

        Args:
            name: The name of the layer.
            acts: An iterable containing the activations that the layer's
                units will be forced to. If its length is less than the number
                of units in the layer, it will be tiled. If its length is
                greater, the extra values will be ignored.

        ValueError: If `name` does not match any existing layer name.

        """
        self._get_layer(name).force(acts)

    def new_projn(self,
                  name: str,
                  pre: str,
                  post: str,
                  spec: specs.ProjnSpec = None) -> None:
        """Adds a new projection to the network.

        Args:
            name: The name of the projection.
            pre: The name of the sending layer.
            post: The name of the receiving layer.
            spec: The projection specification.

        Raises:
            ValueError: If `pre` or `post` do not match any existing layer
                name.
            spec.ValidationError: If the spec contains an invalid parameter
                value.

        """
        if spec is not None:
            spec.validate()

        pre_lr = self._get_layer(pre)
        post_lr = self._get_layer(post)
        pr = projn.Projn(name, pre_lr, post_lr, spec)
        self.projns[name] = pr
        self.objs[name] = pr

    def cycle(self) -> None:
        """Cycles the network."""
        for lg in self.cycle_loggers:
            lg.record()

        for _, lr in self.layers.items():
            lr.activation_cycle()

        for _, pr in self.projns.items():
            pr.flush()

    def logs(self, freq: str, name: str) -> log.Logs:
        """Retrieves logs for an object in the network.

        Args:
            freq: The frequency at which the desired logs were recorded. One
                of `["cycle"]`.
            name: The name of the object for which the logs were recorded.

        Raises:
            ValueError: If the frequency name is invalid, or if no logs were
                recorded for the desired object.

        """
        freq_names = {"cycle": self.cycle_loggers}
        try:
            freq_loggers = freq_names[freq]
        except KeyError:
            raise ValueError("{0} must be one of {1}.".format(
                freq, freq_names.keys()))

        try:
            logger = next(i for i in freq_loggers if i.target_name == name)
        except StopIteration:
            raise ValueError(
                "No logs recorded for object {0}, frequency {1}.".format(
                    name, freq))

        return logger.to_logs()

    def handle(self, event: prg.AtomicEvent) -> None:
        """Overrides events.EventListnerMixin.handle()"""
        if isinstance(event, prg.Cycle):
            self.cycle()
        else:
            for _, obj in self.objs.items():
                obj.handle(event)

    def execute(self, program: prg.Program) -> None:
        """"Executes a prg."""
        for event in program.atomic_stream():
            self.handle(event)
