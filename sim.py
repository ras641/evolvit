import uuid
from typing import List, Tuple, Dict, Optional


class Creature:
    # Class variables (shared defaults)
    MAX_ORGANS = 5
    ALLOWED_ORGANS = ['mouth', 'eye', 'flipper']
    DEFAULT_ENERGY = 100.0
    DEFAULT_HEALTH = 100.0

    def __init__(
        self,
        name: str,
        code: str,
        mutation_rate: float,
        generation: int = 0,
        parent_ids: Optional[List[uuid.UUID]] = None
    ):
        self.id = uuid.uuid4()  # Unique unique identifier
        self.name = name
        self.organs: List[Dict] = []  # Start empty, add via method
        self.code = code
        self.mutation_rate = mutation_rate
        self.generation = generation
        self.parent_ids = parent_ids or []
        self.energy = self.DEFAULT_ENERGY
        self.health = self.DEFAULT_HEALTH
        self.age = 0
        self.reproduction_cooldown = 0

    def add_organ(self, organ_type: str, position: Tuple[float, float], size: float) -> bool:
        """Add an organ to the creature if valid and within limit. Returns True if successful."""
        # Check if max organs reached
        if len(self.organs) >= self.MAX_ORGANS:
            print(f"[ERROR] Cannot add organ: {self.name} already has max organs ({self.MAX_ORGANS}).")
            return False
        # Check for valid organ type
        if organ_type not in self.ALLOWED_ORGANS:
            print(f"[ERROR] Invalid organ type '{organ_type}' for {self.name}. Allowed: {self.ALLOWED_ORGANS}")
            return False
        # Check position and size are valid types
        if not (isinstance(position, tuple) and len(position) == 2 and isinstance(size, (float, int))):
            print(f"[ERROR] Invalid organ parameters for {self.name}. Position must be tuple (x, y), size a number.")
            return False
        # Add the organ
        organ = {
            'type': organ_type,
            'position': position,
            'size': float(size)  # Ensure size is float
        }
        self.organs.append(organ)
        print(f"[INFO] Organ '{organ_type}' added to {self.name}. Total organs: {len(self.organs)}.")
        return True

    def __repr__(self):
        return (f"Creature(id={self.id}, name='{self.name}', organs={self.organs}, "
                f"code='{self.code}', mutation_rate={self.mutation_rate}, "
                f"generation={self.generation}, parent_ids={self.parent_ids}, "
                f"energy={self.energy}, health={self.health}, age={self.age}, "
                f"reproduction_cooldown={self.reproduction_cooldown})")

# Create a creature
creature = Creature(
    name='Swimmy',
    code='MOVE:0.8; EAT:0.5',
    mutation_rate=0.02
)

# Try adding organs
creature.add_organ('mouth', (0.0, 0.0), 1.0)  # ✅
creature.add_organ('eye', (0.5, 0.5), 0.3)    # ✅
creature.add_organ('flipper', (-0.5, -0.5), 0.7)  # ✅
creature.add_organ('wing', (0.1, 0.1), 0.5)   # ❌ Invalid type
creature.add_organ('eye', (0.1,), 0.5)        # ❌ Invalid position
creature.add_organ('mouth', (0.1, 0.2), 'big') # ❌ Invalid size

# Fill to max
for _ in range(5):
    creature.add_organ('eye', (0.0, 0.0), 0.1)  # Will cap at MAX_ORGANS

print(creature)