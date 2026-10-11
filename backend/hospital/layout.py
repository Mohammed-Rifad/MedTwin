"""Where beds are drawn on the floor map (a 1000 x 600 canvas; each unit has its own rectangle)."""

import math

from config.errors import DomainError

PADDING = 20  # space between the unit's edge and its beds
HEADER = 40  # space at the top of the unit for its name
MIN_CELL_WIDTH = 58  # a bed is drawn 54 x 34, so each grid cell needs a little more
MIN_CELL_HEIGHT = 40


class LayoutError(DomainError):
    """Raised when a unit has no room left on the map for another bed."""


def bed_positions(x, y, width, height, rows, cols):
    """Yield the centre point of each bed, laid out in a grid inside the unit's rectangle."""
    cell_width = (width - 2 * PADDING) / cols
    cell_height = (height - HEADER - PADDING) / rows
    for row in range(rows):
        for col in range(cols):
            yield (
                round(x + PADDING + cell_width * (col + 0.5)),
                round(y + HEADER + cell_height * (row + 0.5)),
            )


def max_beds(unit):
    """How many beds fit in the unit's rectangle without overlapping."""
    columns = (unit.map_width - 2 * PADDING) // MIN_CELL_WIDTH
    rows = (unit.map_height - HEADER - PADDING) // MIN_CELL_HEIGHT
    return int(columns * rows)


def grid_for(unit, count):
    """Rows and columns for `count` beds: roughly the unit's shape, without making cells too small."""
    usable_width = unit.map_width - 2 * PADDING
    usable_height = unit.map_height - HEADER - PADDING
    max_columns = max(1, usable_width // MIN_CELL_WIDTH)
    columns = max(1, min(max_columns, count, round(math.sqrt(count * usable_width / usable_height))))
    return math.ceil(count / columns), int(columns)


def check_room_for_another_bed(unit):
    if unit.beds.count() >= max_beds(unit):
        raise LayoutError(f"{unit.name} has no room for another bed on the map (maximum {max_beds(unit)}).")


def arrange_beds(unit):
    """Give every bed in the unit (open or closed) a tidy grid position, in order of bed code."""
    beds = list(unit.beds.order_by("code"))
    if not beds:
        return
    rows, columns = grid_for(unit, len(beds))
    positions = bed_positions(unit.map_x, unit.map_y, unit.map_width, unit.map_height, rows, columns)
    for bed, (x, y) in zip(beds, positions):
        bed.map_x, bed.map_y = x, y
    type(beds[0]).objects.bulk_update(beds, ["map_x", "map_y"])
