"""Placeholder illustrations for Black Spire.

These are flat, low-effort fairytale-style drawings generated with pygame
primitives (see tools/generate_assets.py).  Node 3 owns the real art set; the
only rules here are one consistent style and a farmer drawn from the character
sheet palette so the picture matches the written description.
"""

import os

import pygame


IMAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "images")

ILLUSTRATION_SIZE = (512, 512)


def image_path(image_id):
    return os.path.join(IMAGE_DIR, "%s.png" % image_id)


class Illustrations:
    def __init__(self, image_dir=IMAGE_DIR):
        self.image_dir = image_dir
        self._surfaces = {}

    def load(self, image_id):
        if image_id in self._surfaces:
            return self._surfaces[image_id]
        path = os.path.join(self.image_dir, "%s.png" % image_id)
        if not os.path.exists(path):
            raise FileNotFoundError("missing illustration %s" % path)
        surf = pygame.image.load(path).convert()
        self._surfaces[image_id] = surf
        return surf

    def get(self, image_id):
        return self.load(image_id)
