from typing import Iterator, Set, Union
import attr

from graftlib.eval_ import Dot, Line
from graftlib.round_ import round_stroke


@attr.s
class Elided:
    item: Union[Line, Dot] = attr.ib()


@attr.s
class StrokeOptimiser:
    """
    Adapt a stream of strokes into a stream of strokes that are
    unique after rounding to 1 decimal place.
    For any stroke we are removing because they repeat a previous
    stroke, we emit an Elided instead.
    """

    strokes: Iterator = attr.ib()

    seen_strokes: Set[Union[Dot, Line]] = (
        attr.ib(attr.Factory(set), init=False)
    )

    def __iter__(self):
        return self

    def __next__(self) -> Union[Line, Elided]:
        st = round_stroke(next(self.strokes))
        if st in self.seen_strokes:
            return Elided(st)
        else:
            self.seen_strokes.add(st)
            return st

    def delete_stroke(self, stroke: Union[Dot, Line]):
        """
        Forget that this stroke has been drawn, so if we draw it
        again, it won't be elided.
        """
        self.seen_strokes.remove(stroke)