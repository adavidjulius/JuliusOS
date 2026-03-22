import pygame
import urllib.request
import json
import threading

BG     = (10, 10, 20)
TEXT   = (255, 255, 255)
ACCENT = (0, 200, 255)
GREEN  = (0, 255, 100)
DIM    = (80, 80,   80)
RED    = (255, 80,  80)
YELLOW = (255, 200,  0)

class Weather:
    def __init__(self, screen, font):
        self.screen  = screen
        self.font    = font
        self.city    = ""
        self.data    = None
        self.mode    = "input"
        self.input   = ""
        self.status  = "Enter city name"
        self.loading = False

    def fetch(self, city):
        self.loading = True
        self.status  = f"Fetching {city}..."
        def run():
            try:
                url      = f"https://wttr.in/{city}?format=j1"
                req      = urllib.request.urlopen(url, timeout=5)
                raw      = req.read().decode()
                self.data = json.loads(raw)
                self.mode = "view"
                self.status = "Done"
            except Exception as e:
                self.status  = f"Error: {e}"
                self.mode    = "input"
            self.loading = False
        t = threading.Thread(target=run)
        t.daemon = True
        t.start()

    def get_val(self, key, default="?"):
        try:
            cc = self.data["current_condition"][0]
            return cc.get(key, default)
        except:
            return default

    def draw_input(self):
        self.screen.fill(BG)
        title = self.font.render("Weather", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        status = self.font.render(self.status, True, GREEN)
        self.screen.blit(status, (8, 40))
        inp = self.font.render(f"City: {self.input}_", True, TEXT)
        self.screen.blit(inp, (8, 60))

        hint = self.font.render("ENTER=search  ESC=clear", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def draw_view(self):
        self.screen.fill(BG)
        title = self.font.render("Weather", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        try:
            cc      = self.data["current_condition"][0]
            area    = self.data["nearest_area"][0]
            city    = area["areaName"][0]["value"]
            country = area["country"][0]["value"]
            temp_c  = cc["temp_C"]
            temp_f  = cc["temp_F"]
            feels   = cc["FeelsLikeC"]
            humid   = cc["humidity"]
            wind    = cc["windspeedKmph"]
            desc    = cc["weatherDesc"][0]["value"]

            loc  = self.font.render(f"{city}, {country}", True, ACCENT)
            tmp  = self.font.render(f"{temp_c}C  /  {temp_f}F", True, GREEN)
            fl   = self.font.render(f"Feels like: {feels}C",    True, TEXT)
            dsc  = self.font.render(desc[:26],                  True, YELLOW)
            hum  = self.font.render(f"Humidity : {humid}%",     True, TEXT)
            wnd  = self.font.render(f"Wind     : {wind} km/h",  True, TEXT)

            self.screen.blit(loc, (8, 30))
            pygame.draw.line(self.screen, DIM, (0, 44), (240, 44), 1)
            self.screen.blit(tmp, (8,  50))
            self.screen.blit(fl,  (8,  68))
            self.screen.blit(dsc, (8,  86))
            pygame.draw.line(self.screen, DIM, (0, 102), (240, 102), 1)
            self.screen.blit(hum, (8, 108))
            self.screen.blit(wnd, (8, 126))

            # Forecast
            pygame.draw.line(self.screen, DIM, (0, 144), (240, 144), 1)
            fc_title = self.font.render("Forecast:", True, ACCENT)
            self.screen.blit(fc_title, (8, 148))

            weather = self.data["weather"][:3]
            y       = 164
            for day in weather:
                date   = day["date"]
                maxc   = day["maxtempC"]
                minc   = day["mintempC"]
                fc     = self.font.render(f"{date}  {minc}-{maxc}C", True, TEXT)
                self.screen.blit(fc, (8, y))
                y += 16

        except Exception as e:
            err = self.font.render(f"Parse error: {e}", True, RED)
            self.screen.blit(err, (8, 40))

        hint = self.font.render("ESC=back  R=refresh", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def draw(self):
        if self.mode == "input":
            self.draw_input()
        elif self.mode == "view":
            self.draw_view()

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if self.mode == "input":
                if event.key == pygame.K_RETURN and self.input:
                    self.city = self.input
                    self.fetch(self.city)
                elif event.key == pygame.K_BACKSPACE:
                    self.input = self.input[:-1]
                elif event.key == pygame.K_ESCAPE:
                    self.input = ""
                else:
                    self.input += event.unicode
            elif self.mode == "view":
                if event.key == pygame.K_ESCAPE:
                    self.mode  = "input"
                    self.input = ""
                elif event.key == pygame.K_r:
                    self.fetch(self.city)
