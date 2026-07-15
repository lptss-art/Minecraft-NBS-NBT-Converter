from core.brick import Brick
from core.customNBT import CustomNBT

class LayoutBase(Brick):
    """
    Base class for note layout bricks.
    Handles standard note placement.
    """
    def __init__(self, x=0, y=0, z=0, facing='south', direction=-1):
        super().__init__(x=x, y=y, z=z, facing=facing, direction=direction)
        self.tick = 0

    def add_note_to_brick(self, brick, x, y, z, note):
        """Adds a note block, instrument block below, and air above to a specific brick."""
        if not hasattr(note, 'note'):
            return

        # Ensure indices and string formatting are correct for NBT properties
        instr_index = int(note.instr)
        note_val = str(int(note.note))

        instruments = list(CustomNBT.minecraft_instruments.values())
        instr_name = instruments[instr_index] if instr_index < len(instruments) else "minecraft:dirt"

        brick.add_block(x, y, z, "minecraft:note_block", {"note": note_val}, tick=self.tick)
        brick.add_block(x, y - 1, z, instr_name, {}, tick=self.tick, needs_down=True)
        brick.add_block(x, y + 1, z, "minecraft:air", {}, tick=self.tick)

    def add_note(self, x, y, z, note):
        """Adds a note block, instrument block below, and air above to this brick."""
        self.add_note_to_brick(self, x, y, z, note)

    def add_block(self, x, y, z, block_name, properties=None, tick=0, random_delay_range=-1, needs_down=False, needs_up=False):
        """Adds a generic block to the layout data."""
        if block_name is None:
            return
        super().add_block(x, y, z, block_name, properties=properties, tick=self.tick, random_delay_range=random_delay_range, needs_down=needs_down, needs_up=needs_up)

    def write_nbt(self, nbt_handler):
        """Writes the layout data to the customNBT object."""
        super().write_nbt(nbt_handler)
