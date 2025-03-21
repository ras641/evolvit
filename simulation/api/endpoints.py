from flask import Blueprint, jsonify, request
import uuid

from simulation.creatures import Creature

api_bp = Blueprint('api', __name__)

@api_bp.route('/getstate', methods=['GET'])
def get_state():
    """Get current state of all creatures and food."""
    from simulation.food import food, food_lock  # Avoid circular import

    with Creature.creatures_lock, food_lock:
        return jsonify({
            "creatures": [c.to_dict() for c in Creature.creatures],
            "food": [f.to_dict() for f in food]
        })
    
@api_bp.route('/getforces', methods=['GET'])
def get_forces():
    """Get all forces applied to creatures in the last frame."""
    
    with Creature.creatures_lock:
        return jsonify({
            "forces": Creature.force_log  # ✅ Returns all forces recorded for the last frame
        })

@api_bp.route('/getcreatures', methods=['GET'])
def get_creatures():
    """Return organ data and names for creatures."""
    creature_ids = request.args.getlist('id')

    with Creature.creatures_lock:
        if creature_ids:
            models = [{'id': c.id, 'name': c.name, 'organs': [o.to_dict() for o in c.organs]} for c in Creature.creatures if str(c.id) in creature_ids]
        else:
            models = [{'id': c.id, 'name': c.name, 'organs': [o.to_dict() for o in c.organs]} for c in Creature.creatures]

    return jsonify(models)

@api_bp.route('/getsprites', methods=['GET'])
def get_sprites():
    """Return all sprite layouts and their sprite IDs."""
    with Creature.creatures_lock:  # Ensure thread-safety
        return jsonify(Creature.sprite_map)

@api_bp.route('/uploadcreature', methods=['POST'])
def upload_creature():
    """Upload a new creature to the simulation."""
    data = request.json
    position = data.get("position", [0, 0])
    mutation_rate = float(data.get("mutation_rate", 1.0))
    name = data.get("name", f"Creature_{uuid.uuid4()}")

    if not isinstance(position, list) or len(position) != 2:
        return jsonify({'status': 'error', 'message': 'Invalid position format.'}), 400

    new_creature = Creature(position=position, mutation_rate=mutation_rate, user_created=True, name=name)

    with Creature.creatures_lock:
        Creature.creatures.append(new_creature)

    return jsonify({'status': 'success', 'message': f'Creature {new_creature.id} ({name}) added!'})
