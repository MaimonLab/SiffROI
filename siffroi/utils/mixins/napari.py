from napari.utils.events import EmitterGroup, Event

class ExtractionWithCallback():
    """
    A special mixin for classes that use `napari` further to
    annotate their extraction method or modify them graphically.
    These ROIProtocols do not return an ROI in `extract` despite the
    type hint, but will return an event that will be emitted whose
    source will be the ROI returned
    """

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
    
    def extract(self, *args, **kwargs)->Event:
        pass