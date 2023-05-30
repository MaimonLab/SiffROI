from typing import TYPE_CHECKING, Callable

from napari.utils.events import EmitterGroup, Event

if TYPE_CHECKING:
    from ...roi import ROI

class ExtractionWithCallback():
    """
    A special mixin for classes that use `napari` further to
    annotate their extraction method or modify them graphically.
    These ROIProtocols do not return an ROI from `extract` despite the
    type hint, but will return an event that will be emitted whose
    source will be the ROI returned. Permits an alternate workflow,
    however, in which connect_extraction_callback is called allows
    the ROI returned to be passed to a callback function directly.
    """
    events : EmitterGroup

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self, "events"):
            self.events.add(
                extracted = Event,
            )
        else:
            self.events = EmitterGroup(
                extracted = Event,
            )

    def connect_extraction_callback(self, callback : Callable):
        self._extraction_callback = callback
        self.events.extracted.connect(lambda event: callback(event.source.roi))