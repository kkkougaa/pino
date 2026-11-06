The start screen's freezer fridge.

    pip install bpy                                  # headless Blender
    python fridge.py -- fridge.glb                   # builds the model (add an angle, e.g. 105, to render a preview png instead)
    node pack.js fridge.glb fridge.json              # packs it into the JSON that pino.html embeds (LOBBY_FRIDGE)
