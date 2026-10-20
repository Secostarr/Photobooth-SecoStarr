"""Template definitions for Photobooth v4.0 FASE 2."""

TEMPLATES = {
    "Strip 2": {
        "name": "Strip 2",
        "layout": "Strip Vert",
        "photo_count": 2,
        "description": "2 foto vertikal",
        "icon": "2V",
    },
    "Strip 3": {
        "name": "Strip 3",
        "layout": "Strip Vert",
        "photo_count": 3,
        "description": "3 foto vertikal",
        "icon": "3V",
    },
    "Strip 4": {
        "name": "Strip 4",
        "layout": "Strip Vert",
        "photo_count": 4,
        "description": "4 foto vertikal",
        "icon": "4V",
    },
    "Strip H2": {
        "name": "Strip H2",
        "layout": "Strip Horiz",
        "photo_count": 2,
        "description": "2 foto horizontal",
        "icon": "2H",
    },
    "Strip H3": {
        "name": "Strip H3",
        "layout": "Strip Horiz",
        "photo_count": 3,
        "description": "3 foto horizontal",
        "icon": "3H",
    },
    "Grid 2x2": {
        "name": "Grid 2x2",
        "layout": "Grid 2x2",
        "photo_count": 4,
        "description": "Grid 2x2 (4 foto)",
        "icon": "2x2",
    },
    "Single": {
        "name": "Single",
        "layout": "Single",
        "photo_count": 1,
        "description": "1 foto tunggal",
        "icon": "1",
    },
}

TEMPLATE_NAMES = list(TEMPLATES.keys())


def get_template(name):
    return TEMPLATES.get(name, TEMPLATES["Strip 4"])
