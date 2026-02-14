from __future__ import annotations

import random
try:
    from typing import Iterable
except ImportError:  # MicroPython fallback
    Iterable = object  # type: ignore[assignment]

from .codee_audio import CodeeAudio
from .codee_display import BLACK, WHITE, CodeeDisplay, rgb565
from .codee_input import BUTTON_A, BUTTON_B, BUTTON_C, BUTTON_D, CodeeInput
from .codee_save import CodeeSave

TOOL_ROAD = "road"
TOOL_POWER = "power"
TOOL_PARK = "park"
TOOL_RESIDENTIAL = "res"
TOOL_COMMERCIAL = "com"
TOOL_INDUSTRIAL = "ind"
TOOL_BULLDOZE = "bulldoze"

TOOLS = [
    TOOL_ROAD,
    TOOL_POWER,
    TOOL_PARK,
    TOOL_RESIDENTIAL,
    TOOL_COMMERCIAL,
    TOOL_INDUSTRIAL,
    TOOL_BULLDOZE,
]

BUILD_COST = {
    TOOL_ROAD: 4,
    TOOL_POWER: 45,
    TOOL_PARK: 10,
    TOOL_RESIDENTIAL: 16,
    TOOL_COMMERCIAL: 20,
    TOOL_INDUSTRIAL: 24,
}

MAINTENANCE_COST = {
    TOOL_ROAD: 1,
    TOOL_POWER: 10,
    TOOL_PARK: 2,
}

ZONE_TYPES = {TOOL_RESIDENTIAL, TOOL_COMMERCIAL, TOOL_INDUSTRIAL}

TILE_WATER = "water"
TILE_EMPTY = "empty"


class TinyCityModel:
    """TinyCity-inspired strategy model for Codee.

    This model keeps all game rules deterministic and side-effect free.
    Rendering/input/storage are handled in `TinyCityApp`.
    """

    def __init__(self, width: int = 10, height: int = 8, seed: int | None = None) -> None:
        self.width = width
        self.height = height
        self._rng = random.Random(seed)

        self.tiles: list[list[str]] = []
        self.zone_level: list[list[int]] = []

        self.cursor_x = 0
        self.cursor_y = 0
        self.selected_tool_index = 0

        self.year = 1
        self.money = 220
        self.population = 0
        self.last_event = ""
        self.game_over = False

        self._reset_map()

    def _reset_map(self) -> None:
        self.tiles = []
        self.zone_level = []
        for y in range(self.height):
            tile_row: list[str] = []
            level_row: list[int] = []
            for x in range(self.width):
                water_chance = 0.06 if 0 < x < self.width - 1 and 0 < y < self.height - 1 else 0.0
                tile_row.append(TILE_WATER if self._rng.random() < water_chance else TILE_EMPTY)
                level_row.append(0)
            self.tiles.append(tile_row)
            self.zone_level.append(level_row)

    @property
    def current_tool(self) -> str:
        return TOOLS[self.selected_tool_index % len(TOOLS)]

    def set_tool(self, tool: str) -> None:
        self.selected_tool_index = TOOLS.index(tool)

    def cycle_tool(self, step: int = 1) -> None:
        self.selected_tool_index = (self.selected_tool_index + step) % len(TOOLS)

    def move_cursor(self, dx: int, dy: int) -> None:
        self.cursor_x = (self.cursor_x + dx) % self.width
        self.cursor_y = (self.cursor_y + dy) % self.height

    def _count_tiles(self, tile: str) -> int:
        return sum(1 for row in self.tiles for value in row if value == tile)

    def _iter_zone_cells(self) -> Iterable[tuple[int, int, str]]:
        for y in range(self.height):
            for x in range(self.width):
                tile = self.tiles[y][x]
                if tile in ZONE_TYPES:
                    yield x, y, tile

    def _is_adjacent_to(self, x: int, y: int, tile: str) -> bool:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx = x + dx
            ny = y + dy
            if 0 <= nx < self.width and 0 <= ny < self.height and self.tiles[ny][nx] == tile:
                return True
        return False

    def _can_build_on(self, tile: str) -> bool:
        return tile in {TILE_EMPTY}

    def place_current_tool(self) -> tuple[bool, str]:
        if self.game_over:
            return False, "Game over"

        x, y = self.cursor_x, self.cursor_y
        tile = self.tiles[y][x]
        tool = self.current_tool

        if tool == TOOL_BULLDOZE:
            if tile in {TILE_WATER, TILE_EMPTY}:
                return False, "Nothing to bulldoze"
            self.tiles[y][x] = TILE_EMPTY
            self.zone_level[y][x] = 0
            self.last_event = "Bulldozed"
            return True, self.last_event

        if tile == TILE_WATER:
            return False, "Water tile"

        if not self._can_build_on(tile):
            return False, "Occupied"

        cost = BUILD_COST[tool]
        if self.money < cost:
            return False, "No money"

        self.money -= cost
        self.tiles[y][x] = tool
        self.zone_level[y][x] = 1 if tool in ZONE_TYPES else 0
        self.last_event = f"Built {tool}"
        return True, self.last_event

    def _update_population(self) -> None:
        pop = 0
        for x, y, tile in self._iter_zone_cells():
            level = self.zone_level[y][x]
            if tile == TOOL_RESIDENTIAL:
                pop += level * 6
            elif tile == TOOL_COMMERCIAL:
                pop += level * 3
            elif tile == TOOL_INDUSTRIAL:
                pop += level * 2
        self.population = pop

    def _grow_zones(self) -> int:
        growth = 0
        com_count = self._count_tiles(TOOL_COMMERCIAL)
        ind_count = self._count_tiles(TOOL_INDUSTRIAL)
        has_power = self._count_tiles(TOOL_POWER) > 0

        for x, y, tile in list(self._iter_zone_cells()):
            level = self.zone_level[y][x]
            if level >= 3:
                continue

            near_road = self._is_adjacent_to(x, y, TOOL_ROAD)
            growth_score = 0
            if near_road:
                growth_score += 1
            if has_power:
                growth_score += 1
            if tile == TOOL_RESIDENTIAL and com_count > 0 and ind_count > 0:
                growth_score += 1
            if tile == TOOL_COMMERCIAL and self.population > 20:
                growth_score += 1
            if tile == TOOL_INDUSTRIAL and has_power:
                growth_score += 1

            chance = 0.12 + 0.18 * growth_score
            if self._rng.random() < min(0.88, chance):
                self.zone_level[y][x] += 1
                growth += 1

        return growth

    def _maybe_disaster(self) -> str:
        if self._rng.random() > 0.10:
            return ""

        candidates: list[tuple[int, int]] = []
        for y in range(self.height):
            for x in range(self.width):
                tile = self.tiles[y][x]
                if tile not in {TILE_EMPTY, TILE_WATER}:
                    candidates.append((x, y))
        if not candidates:
            return ""

        x, y = self._rng.choice(candidates)
        if self.tiles[y][x] in ZONE_TYPES and self.zone_level[y][x] > 1:
            self.zone_level[y][x] -= 1
            return "Disaster: district damaged"

        self.tiles[y][x] = TILE_EMPTY
        self.zone_level[y][x] = 0
        return "Disaster: structure lost"

    def end_year(self) -> dict:
        if self.game_over:
            return {
                "year": self.year,
                "money": self.money,
                "population": self.population,
                "revenue": 0,
                "maintenance": 0,
                "growth": 0,
                "event": "",
            }

        self.year += 1
        growth = self._grow_zones()
        self._update_population()

        residential = self._count_tiles(TOOL_RESIDENTIAL)
        commercial = self._count_tiles(TOOL_COMMERCIAL)
        industrial = self._count_tiles(TOOL_INDUSTRIAL)

        revenue = self.population * 2 + commercial * 6 + industrial * 8
        maintenance = (
            self._count_tiles(TOOL_ROAD) * MAINTENANCE_COST[TOOL_ROAD]
            + self._count_tiles(TOOL_PARK) * MAINTENANCE_COST[TOOL_PARK]
            + self._count_tiles(TOOL_POWER) * MAINTENANCE_COST[TOOL_POWER]
        )

        self.money += revenue - maintenance
        event = self._maybe_disaster()

        if self.money < -250:
            self.game_over = True
            event = "Bankrupt"

        if growth > 0 and not event:
            event = f"Growth +{growth}"
        self.last_event = event

        return {
            "year": self.year,
            "money": self.money,
            "population": self.population,
            "revenue": revenue,
            "maintenance": maintenance,
            "growth": growth,
            "residential": residential,
            "commercial": commercial,
            "industrial": industrial,
            "event": event,
        }

    def to_dict(self) -> dict:
        return {
            "width": self.width,
            "height": self.height,
            "tiles": self.tiles,
            "zone_level": self.zone_level,
            "cursor_x": self.cursor_x,
            "cursor_y": self.cursor_y,
            "selected_tool_index": self.selected_tool_index,
            "year": self.year,
            "money": self.money,
            "population": self.population,
            "last_event": self.last_event,
            "game_over": self.game_over,
        }

    def from_dict(self, data: dict) -> None:
        self.width = int(data.get("width", self.width))
        self.height = int(data.get("height", self.height))

        tiles = data.get("tiles")
        levels = data.get("zone_level")
        if isinstance(tiles, list) and isinstance(levels, list):
            self.tiles = [list(row)[: self.width] for row in tiles[: self.height]]
            self.zone_level = [list(row)[: self.width] for row in levels[: self.height]]
        else:
            self._reset_map()

        self.cursor_x = int(data.get("cursor_x", 0)) % self.width
        self.cursor_y = int(data.get("cursor_y", 0)) % self.height
        self.selected_tool_index = int(data.get("selected_tool_index", 0)) % len(TOOLS)
        self.year = int(data.get("year", 1))
        self.money = int(data.get("money", 220))
        self.population = int(data.get("population", 0))
        self.last_event = str(data.get("last_event", ""))
        self.game_over = bool(data.get("game_over", False))

        if len(self.tiles) != self.height or any(len(row) != self.width for row in self.tiles):
            self._reset_map()


class TinyCityApp:
    """Input/render shell for TinyCityModel on Codee."""

    def __init__(
        self,
        display: CodeeDisplay,
        input_state: CodeeInput,
        audio: CodeeAudio,
        save: CodeeSave,
        seed: int | None = None,
    ) -> None:
        self.display = display
        self.input = input_state
        self.audio = audio
        self.save = save

        self.model = TinyCityModel(seed=seed)
        self.wants_exit = False

        self._combo_frames: dict[str, int] = {}
        self._combo_latched: dict[str, bool] = {}

        state = self.save.load(default={})
        if state:
            self.model.from_dict(state)

    def _persist(self) -> None:
        self.save.save(self.model.to_dict())

    def _combo_ready(self, name: str, active: bool, threshold: int) -> bool:
        if not active:
            self._combo_frames[name] = 0
            self._combo_latched[name] = False
            return False

        self._combo_frames[name] = self._combo_frames.get(name, 0) + 1
        if self._combo_frames[name] < threshold:
            return False

        if self._combo_latched.get(name, False):
            return False

        self._combo_latched[name] = True
        return True

    def step(self) -> None:
        self.input.update()

        if self._combo_ready(
            "exit",
            self.input.pressed(BUTTON_A)
            and self.input.pressed(BUTTON_C)
            and self.input.pressed(BUTTON_D),
            threshold=8,
        ):
            self.wants_exit = True
            return

        if (
            self.input.just_pressed(BUTTON_A)
            and not self.input.pressed(BUTTON_B)
            and not self.input.pressed(BUTTON_C)
            and not self.input.pressed(BUTTON_D)
        ):
            self.model.move_cursor(-1, 0)
        elif (
            self.input.just_pressed(BUTTON_B)
            and not self.input.pressed(BUTTON_A)
            and not self.input.pressed(BUTTON_C)
            and not self.input.pressed(BUTTON_D)
        ):
            self.model.move_cursor(1, 0)
        elif (
            self.input.just_pressed(BUTTON_C)
            and not self.input.pressed(BUTTON_A)
            and not self.input.pressed(BUTTON_B)
            and not self.input.pressed(BUTTON_D)
        ):
            self.model.move_cursor(0, -1)
        elif (
            self.input.just_pressed(BUTTON_D)
            and not self.input.pressed(BUTTON_A)
            and not self.input.pressed(BUTTON_B)
            and not self.input.pressed(BUTTON_C)
        ):
            self.model.move_cursor(0, 1)

        if self._combo_ready(
            "tool_cycle",
            self.input.pressed(BUTTON_A) and self.input.pressed(BUTTON_B),
            threshold=4,
        ):
            self.model.cycle_tool(1)
            self.audio.move_sound()

        if self._combo_ready(
            "build",
            self.input.pressed(BUTTON_C) and self.input.pressed(BUTTON_D),
            threshold=4,
        ):
            ok, _message = self.model.place_current_tool()
            if ok:
                self.audio.merge_sound()
                self._persist()
            else:
                self.audio.tone(260, 45)

        if self._combo_ready(
            "year",
            self.input.pressed(BUTTON_A) and self.input.pressed(BUTTON_D),
            threshold=4,
        ):
            self.model.end_year()
            self._persist()
            self.audio.tone(620, 45)

        self.render()

    def render(self) -> None:
        sky = rgb565(22, 30, 40)
        water = rgb565(38, 94, 168)
        ground = rgb565(68, 95, 57)
        road = rgb565(78, 78, 78)
        power = rgb565(224, 196, 68)
        park = rgb565(46, 140, 74)
        residential = rgb565(92, 183, 92)
        commercial = rgb565(109, 151, 219)
        industrial = rgb565(185, 132, 77)

        self.display.clear(sky)
        self.display.text(f"TinyCity Y{self.model.year}", 2, 2, WHITE)
        self.display.text(f"${self.model.money} P{self.model.population}", 2, 10, WHITE)

        tile_color = {
            TILE_WATER: water,
            TILE_EMPTY: ground,
            TOOL_ROAD: road,
            TOOL_POWER: power,
            TOOL_PARK: park,
            TOOL_RESIDENTIAL: residential,
            TOOL_COMMERCIAL: commercial,
            TOOL_INDUSTRIAL: industrial,
        }

        tile_size = 10
        map_w = self.model.width * tile_size
        map_h = self.model.height * tile_size
        map_x = (self.display.width - map_w) // 2
        map_y = 24

        for y in range(self.model.height):
            for x in range(self.model.width):
                tile = self.model.tiles[y][x]
                color = tile_color.get(tile, ground)
                x0 = map_x + x * tile_size
                y0 = map_y + y * tile_size
                self.display.fill_rect(x0, y0, tile_size - 1, tile_size - 1, color)

                level = self.model.zone_level[y][x]
                if tile in ZONE_TYPES and level > 0:
                    for i in range(level):
                        self.display.fill_rect(x0 + 1 + i * 2, y0 + tile_size - 3, 1, 2, BLACK)

        cursor_px = map_x + self.model.cursor_x * tile_size
        cursor_py = map_y + self.model.cursor_y * tile_size
        self.display.rect(cursor_px, cursor_py, tile_size - 1, tile_size - 1, WHITE)

        tool_label = self.model.current_tool.upper()
        self.display.text(f"Tool:{tool_label}", 2, 110, WHITE)

        event = self.model.last_event[:16] if self.model.last_event else "AB tool CD build"
        self.display.text(event, 2, 118, WHITE)

        if self.model.game_over:
            self.display.fill_rect(8, 52, 112, 20, rgb565(170, 60, 60))
            self.display.center_text("CITY BANKRUPT", 58, WHITE)

        self.display.present()
