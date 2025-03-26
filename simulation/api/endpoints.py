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



@api_bp.route('/getfull', methods=['GET'])
def get_full_state():
    x = request.args.get('x', default=0, type=int)
    y = request.args.get('y', default=0, type=int)

    if world.get_built_index() is None:
        return jsonify({ "status": "pending", "message": "Delta buffer not available yet. Please try again shortly." })

    try:
        cell = world.cell_grid[y][x]
    except IndexError:
        return jsonify({'status': 'error', 'message': 'Cell not found'}), 404

    with cell.lock:
        state_data = cell.get_full()

        # Include all sprites inline
        import simulation.simulation.creatures as creature_mod
        sprite_data = {}
        with creature_mod.Creature.sprite_lock:
            for sprite_id, value in creature_mod.Creature.sprite_map.items():
                layout = value.get("layout") if isinstance(value, dict) else value
                sprite_data[sprite_id] = layout

            state_data["sprites"] = sprite_data

        return jsonify(state_data)
    
@api_bp.route('/getstate', methods=['GET'])
def get_state():


    x = request.args.get('x', default=0, type=int)
    y = request.args.get('y', default=0, type=int)

    if world.get_built_index() is None:
        return jsonify({ "status": "pending", "message": "Delta buffer not available yet. Please try again shortly." })

    try:
        cell = world.cell_grid[y][x]

    except IndexError:
        return jsonify({'status': 'error', 'message': 'Cell not found'}), 404

    with cell.lock:
        return jsonify(cell.get_live_state())

@api_bp.route('/getdeltas', methods=['GET'])
def get_deltas():
    x = request.args.get('x', default=0, type=int)
    y = request.args.get('y', default=0, type=int)

    if world.get_built_index() is None:
        return jsonify({ "status": "pending", "message": "Delta buffer not available yet. Please try again shortly." })

    try:
        cell = world.cell_grid[y][x]
    except IndexError:
        return jsonify({'status': 'error', 'message': 'Cell not found'}), 404

    with cell.lock:
        return jsonify({
            "frame": world.get_frame(),
            "deltas": cell.get_deltas(),
        })

@api_bp.route('/getsprites', methods=['GET'])
def get_sprites():
    import simulation.simulation.creatures as creature_mod

    sprite_data = {}
    with creature_mod.Creature.sprite_lock:
        for sprite_id, value in creature_mod.Creature.sprite_map.items():
            layout = value.get("layout") if isinstance(value, dict) else value
            sprite_data[sprite_id] = layout

    return jsonify(sprite_data)

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



@api_bp.route('/uploadcreature', methods=['POST'])
def upload_creature():
    import simulation.simulation.creatures as creature_mod

    cell = world.cell_grid[0][0]
    data = request.get_json()

    position = data.get("position", None)  # optional
    organs = data.get("organs", [])
    name = data.get("name", None)

    try:
        new_creature = creature_mod.Creature(
            position=position,  # may be None
            organs=organs,
            name=name,
            user_created=True
        )

        with cell.lock:
            if new_creature.isAlive:
                cell.add(new_creature)
            else:
                return jsonify({"error": "Creature creation failed (invalid organs or dead)"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({
        "message": "✅ Creature created",
        "creature_id": new_creature.id,
        "position": new_creature.position,
        "organs": [o.to_dict() for o in new_creature.organs]
    })
