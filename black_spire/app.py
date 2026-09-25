"""The Black Spire windowed app (proof-of-concept engine).

Runs the slice in a pygame window: illustration on the left, story text and
choices on the right, an ambient bed always playing, action sounds layered on
choice, and the death bell on death.

Run:

    python3 -m black_spire

Headless / test flags (all optional, keep the app CI-friendly):

    --frames N    auto-quit after N frames (for headless / smoke runs)
    --scene ID    start at a given scene id
    --list        print the scene graph and exit
"""

import argparse
import sys

import pygame

from . import art, audio, story


WIDTH, HEIGHT = 1024, 640
ILL_W, ILL_H = art.ILLUSTRATION_SIZE          # 512x512
ILL_X, ILL_Y = 24, 24
TEXT_X = ILL_X + ILL_W + 40                    # right panel start
TEXT_W = WIDTH - TEXT_X - 24

BG_COLOR = (18, 20, 26)
PANEL_BG = (28, 31, 40)
BORDER = (90, 96, 110)
TITLE_COLOR = (240, 236, 220)
BODY_COLOR = (226, 222, 210)
CHOICE_COLOR = (250, 246, 232)
CHOICE_BG = (44, 52, 62)
CHOICE_BG_HOVER = (64, 74, 88)


class Game:
    def __init__(self, start_scene=None, size=(WIDTH, HEIGHT)):
        pygame.init()
        mixer_ok = False
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(22050, -16, 1, 512)
            mixer_ok = pygame.mixer.get_init() is not None
            if mixer_ok:
                pygame.mixer.set_num_channels(16)
                pygame.mixer.set_reserved(1)  # channel 0 = ambient bed
        except pygame.error:
            mixer_ok = False

        self.screen = pygame.display.set_mode(size)
        pygame.display.set_caption("Black Spire \u2014 a fairytale slice")
        self.clock = pygame.time.Clock()
        self.font_title = pygame.font.SysFont("dejavusans", 30, bold=True)
        self.font_body = pygame.font.SysFont("dejavusans", 21)
        self.font_choice = pygame.font.SysFont("dejavusans", 20)

        self.story = story.StoryEngine(start=start_scene)
        self.illustrations = art.Illustrations()
        self.audio = audio.AudioManager(enabled=mixer_ok)
        self.running = True
        self.choice_rects = []
        self.hover = None

        self._enter_scene(self.story.scene().id)

    # -- scene transitions --------------------------------------------
    def _enter_scene(self, scene_id):
        scene = self.story.scenes[scene_id]
        self.illustrations.load(scene.image)
        self.hover = None
        self.choice_rects = []
        if scene_id == story.DEATH_SCENE:
            self.audio.stop_ambient()
            self.audio.play_bell()
        else:
            self.audio.play_ambient(scene.ambient)

    def navigate(self, choice_index):
        choice = self.story.choices()[choice_index]
        if choice.action_sound:
            self.audio.play_action(choice.action_sound)
        new_id = self.story.choose(choice_index)
        self._enter_scene(new_id)
        return new_id

    # -- rendering ----------------------------------------------------
    def _wrap(self, text, font, max_width):
        lines = []
        for raw in text.split("\n"):
            words = raw.split(" ")
            cur = ""
            for w in words:
                trial = (cur + " " + w).strip()
                if not cur or font.size(trial)[0] <= max_width:
                    cur = trial
                else:
                    lines.append(cur)
                    cur = w
            if cur:
                lines.append(cur)
            lines.append("")  # blank line for explicit paragraph break
        return lines

    def render(self):
        self.screen.fill(BG_COLOR)

        # left: illustration inside a framed panel
        ill = self.illustrations.get(self.story.scene().image)
        panel = pygame.Surface((ILL_W + 16, ILL_H + 16))
        panel.fill(PANEL_BG)
        pygame.draw.rect(panel, BORDER, panel.get_rect(), 2)
        panel.blit(ill, (8, 8))
        self.screen.blit(panel, (ILL_X - 8, ILL_Y - 8))

        # right: title + body text + choices
        y = 24
        title = self.font_title.render(self.story.scene().title, True, TITLE_COLOR)
        self.screen.blit(title, (TEXT_X, y))
        y += title.get_height() + 18

        for line in self._wrap(self.story.scene().text, self.font_body, TEXT_W):
            if line == "":
                y += 10
                continue
            surf = self.font_body.render(line, True, BODY_COLOR)
            self.screen.blit(surf, (TEXT_X, y))
            y += surf.get_height() + 4

        y += 20
        self.choice_rects = []
        for i, choice in enumerate(self.story.choices()):
            label = "%d. %s" % (i + 1, choice.label)
            surf = self.font_choice.render(label, True, CHOICE_COLOR)
            pad = 14
            rect = pygame.Rect(TEXT_X, y, TEXT_W, surf.get_height() + pad)
            color = CHOICE_BG_HOVER if self.hover == i else CHOICE_BG
            pygame.draw.rect(self.screen, color, rect, border_radius=6)
            pygame.draw.rect(self.screen, BORDER, rect, 2, border_radius=6)
            self.screen.blit(surf, (TEXT_X + pad, y + pad // 2))
            self.choice_rects.append(rect)
            y += rect.height + 12

        pygame.display.flip()
        return {
            "illustration": ill.get_size(),
            "title": title.get_size(),
            "choices": len(self.choice_rects),
        }

    # -- input ---------------------------------------------------------
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False
            elif pygame.K_1 <= event.key <= pygame.K_9:
                idx = event.key - pygame.K_1
                if idx < len(self.story.choices()):
                    self.navigate(idx)
        elif event.type == pygame.MOUSEMOTION:
            self.hover = self._choice_at(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            idx = self._choice_at(event.pos)
            if idx is not None:
                self.navigate(idx)

    def _choice_at(self, pos):
        for i, r in enumerate(self.choice_rects):
            if r.collidepoint(pos):
                return i
        return None

    # -- main loop -----------------------------------------------------
    def run(self, max_frames=None):
        frames = 0
        while self.running:
            for event in pygame.event.get():
                self.handle_event(event)
            self.render()
            self.clock.tick(60)
            frames += 1
            if max_frames is not None and frames >= max_frames:
                break
        pygame.quit()
        return frames


def main(argv=None):
    parser = argparse.ArgumentParser(description="Black Spire \u2014 proof-of-concept slice")
    parser.add_argument("--frames", type=int, default=None,
                        help="auto-quit after N frames (headless/CI)")
    parser.add_argument("--scene", default=None, help="start at a given scene id")
    parser.add_argument("--list", action="store_true",
                        help="print the scene graph and exit")
    args = parser.parse_args(argv)

    if args.list:
        for sid, scene in story.SCENES.items():
            print("[%s] %s" % (sid, scene.title))
            for i, c in enumerate(scene.choices):
                extra = "  (sound: %s)" % c.action_sound if c.action_sound else ""
                print("    %d. %s  -> %s%s" % (i + 1, c.label, c.target, extra))
        return 0

    if args.scene is not None and args.scene not in story.SCENES:
        print("unknown scene %r; valid: %s" % (args.scene, ", ".join(story.SCENES)),
              file=sys.stderr)
        return 2

    game = Game(start_scene=args.scene)
    game.run(max_frames=args.frames)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
