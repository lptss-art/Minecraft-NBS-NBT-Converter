from core.brick import Brick

class LayoutBase(Brick):
    """
    Base class for note layout bricks.
    Handles NBT initialization, common indexes, and standard note placement.
    """
    def __init__(self, x=0, y=0, z=0, nbt=None, facing='south', direction=-1):
        super().__init__(x=x, y=y, z=z, nbt=nbt, facing=facing, direction=direction)

        self.custom_nbt = nbt
        self.tick = 0

        if nbt:
            self.index_stone = self.custom_nbt.get_index_safe("minecraft:stone")
            self.index_wood = self.custom_nbt.get_index_safe("minecraft:oak_planks")
            self.index_redstone = self.custom_nbt.get_index_safe("minecraft:redstone_wire")
            self.index_piston = self.custom_nbt.index_pistons["east"]
            self.index_redstone_block = self.custom_nbt.get_index_safe("minecraft:redstone_block")
            self.index_repeater = self.custom_nbt.index_repeaters["west"]
            self.index_air = self.custom_nbt.get_index_safe("minecraft:air")
            self.index_rail = self.custom_nbt.get_index_safe("minecraft:powered_rail", {"shape": "east_west"})
            self.index_detector = self.custom_nbt.get_index_safe("minecraft:detector_rail", {"shape": "east_west"})

            self.offset_notes = self.custom_nbt.index_notes
            self.offset_instr = self.custom_nbt.index_instr
            self.index_floor = -1  # Default fallback before cleanup
        else:
            self.index_stone = -1
            self.index_wood = -1
            self.index_redstone = -1
            self.index_piston = -1
            self.index_redstone_block = -1
            self.index_repeater = -1
            self.index_air = -1
            self.index_rail = -1
            self.index_detector = -1
            self.offset_notes = -1
            self.offset_instr = -1
            self.index_floor = -1

    def add_note_to_brick(self, brick, x, y, z, note):
        """Adds a note block, instrument block below, and air above to a specific brick."""
        if not hasattr(note, 'note'):
            return
        # Because we call add_block on `brick` (which could be a raw Brick or LayoutBase),
        # we check the signature or pass the positional args explicitly.
        # `Brick.add_block` expects (x, y, z, index, tick=0, ...)
        brick.add_block(x, y, z, note.note + self.offset_notes, self.tick)
        brick.add_block(x, y - 1, z, note.instr + self.offset_instr, self.tick, needs_down=True)
        brick.add_block(x, y + 1, z, self.index_air, self.tick)

    def add_note(self, x, y, z, note):
        """Adds a note block, instrument block below, and air above to this brick."""
        self.add_note_to_brick(self, x, y, z, note)

    def add_block(self, x, y, z, index, tick=0, random_delay_range=-1, needs_down=False, needs_up=False):
        """Adds a generic block to the layout data."""
        if index == -1:
            return
        super().add_block(x, y, z, index, self.tick, random_delay_range=random_delay_range, needs_down=needs_down, needs_up=needs_up)

    def write_nbt(self):
        """Writes the layout data to the customNBT object."""
        super().write_nbt(self.custom_nbt)
