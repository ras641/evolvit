from flask import Blueprint, jsonify, request, render_template
import uuid
import os


from simulation.simulation.world import world

api_bp = Blueprint('api', __name__)



@api_bp.route('/viewer')
def viewer_page():
    """Render the canvas viewer with live creature/food state injected."""
    from simulation.simulation.creatures import Creature

    cell = world.cell_grid[0][0]

    with cell.lock:
        creatures = [c.to_dict() for c in cell.creatures]
        food = [f.to_dict() for f in cell.food]

    return render_template("viewer.html", sprites=Creature.sprite_map, creatures=creatures, food=food)



@api_bp.route('/getstate', methods=['GET'])
def get_state():
    x = request.args.get('x', type=int)
    y = request.args.get('y', type=int)

    if world.get_built_index() is None:
        return jsonify({ "status": "pending", "message": "Delta buffer not available yet. Please try again shortly." })

    if x is None or y is None:
        return jsonify({'status': 'error', 'message': 'Please specify x and y position of cell'}), 400

    try:
        cell = world.cell_grid[y][x]  # Note: grid is [y][x]
    except IndexError:
        return jsonify({'status': 'error', 'message': 'Cell not found'}), 404

    with cell.lock:
        state_data = cell.get_state()

        # 🔁 Include all sprites
        import simulation.simulation.creatures as creature_mod  # lazy import

        sprite_data = []
        with creature_mod.Creature.sprite_lock:
            for sprite_id, value in creature_mod.Creature.sprite_map.items():
                layout = value.get("layout") if isinstance(value, dict) else value
                sprite_data.append({
                    "id": sprite_id,
                    "layout": layout
                })

        # 🧪 Add sprite list to state payload
        state_data["sprites"] = sprite_data

        return jsonify(state_data)
    

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
    """Return all sprite layouts by sprite ID."""

    import simulation.simulation.creatures as creature_mod  # lazy full module import

    layout_data = []

    with creature_mod.Creature.sprite_lock:
        for sprite_id, value in creature_mod.Creature.sprite_map.items():
            layout = value.get("layout") if isinstance(value, dict) else value

            layout_data.append({
                "id": sprite_id,
                "layout": layout
            })

    return jsonify(layout_data)


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
