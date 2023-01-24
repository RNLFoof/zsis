from dataclasses import dataclass
from functools import cached_property


@dataclass
class SourcerSettings:
    scale_x: int
    scale_y: int
    factor_divider: int
    bw: bool = True
    scaling: bool = True
    resample: int = 2

    @cached_property
    def rep_str(self):
        return f'-{self.scale_x}-{self.scale_y}-{self.factor_divider}-{self.bw}-{self.scaling}-{self.resample}'
