import sqlite3
from dataclasses import dataclass
from typing import Optional, Iterable


@dataclass
class Report:
    files_scanned: int = 0
    sourceables_added: int = 0
    color_hashes_added: int = 0
    sources_added: int = 0

    def update_with(self, sourceable_cursor: Optional[sqlite3.Cursor], color_hash_cursor: Optional[sqlite3.Cursor],
                    source_cursors: Optional[Iterable[sqlite3.Cursor]]):
        self.files_scanned += 1
        self.sourceables_added += int(sourceable_cursor is not None)
        self.color_hashes_added += int(color_hash_cursor is not None)
        self.sources_added += sum([int(x is not None) for x in source_cursors])

    def __str__(self):
        s = f"Scanned {self.files_scanned} files: "

        adds = []
        for var, name in [
            (self.sourceables_added, "sourcable(s)"),
            (self.color_hashes_added, "color hash(es)"),
            (self.sources_added, "source(s)"),
        ]:
            if var > 0:
                adds.append(f"{var} {name}")

        if len(adds) == 0:
            s += f"No changes."
        else:
            s += f"Added {', '.join(adds)}."

        return s
