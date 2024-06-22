from flask import Flask, request, jsonify
app = Flask(__name__)
items = []
debug_mode = True

@app.route('/create', methods=['POST'])
def create():
    if debug_mode:
        items.append(request.get_json())
    return jsonify({'message': 'Item created successfully.'}), 201

@app.route('/read-all')
def read\_all():
    return jsonify(items)

@app.route('/read-one/<id>')
def read\_one(id):
    for item in items:
        if str(item['id']) == id:
            return jsonify(item),
        404
    return jsonify({'message': 'Item not found.'}), 404

@app.route('/update', methods=['PUT'])
def update():
    if debug_mode:
        updated\_item = request.get\_json()
        for index, item in enumerate(items):
            if str(item['id']) == updated\_item['id']:
                items[index] = updated\_item
        return jsonify({'message': 'Item updated successfully.'}), 200
    return jsonify({'message': 'Error: Debug mode not enabled.'}), 503

@app.route('/delete/<id>')
def delete(id):
    if debug_mode:
        items = [item for item in items if str(item['id']) != id]
    return jsonify({'message': 'Item deleted successfully.'}), 200
    return jsonify({'message': 'Error: Debug mode not enabled.'}), 503