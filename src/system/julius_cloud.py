import pygame
import threading
import socket
import json
import os
import hashlib
import time

BG     = (18, 18, 22)
CARD   = (28, 28, 34)
WHITE  = (255, 255, 255)
DIM    = (120, 120, 130)
BLUE   = (10, 132, 255)
GREEN  = (48, 209, 88)
PURPLE = (191, 90, 242)

CLOUD_DIR   = "/var/julius/cloud/"
SYNC_FILE   = "/etc/julius/cloud_sync.conf"
CLOUD_PORT  = 9978

class JuliusCloud:
    def __init__(self, screen, font, font_small):
        self.screen     = screen
        self.font       = font
        self.font_small = font_small
        self.W          = screen.get_width()
        self.H          = screen.get_height()
        self.visible    = False
        self.status     = "Idle"
        self.syncing    = False
        self.files      = []
        self.server_ip  = ""
        self.last_sync  = "Never"
        os.makedirs(CLOUD_DIR, exist_ok=True)
        self.load_config()

    def load_config(self):
        if os.path.exists(SYNC_FILE):
            with open(SYNC_FILE) as f:
                for line in f:
                    if "server=" in line:
                        self.server_ip = line.split("=")[1].strip()
                    elif "last_sync=" in line:
                        self.last_sync = line.split("=")[1].strip()

    def save_config(self):
        with open(SYNC_FILE, "w") as f:
            f.write(f"server={self.server_ip}\n")
            f.write(f"last_sync={self.last_sync}\n")

    def file_hash(self, path):
        h = hashlib.sha256()
        with open(path,"rb") as f:
            for chunk in iter(lambda:f.read(4096),b""):
                h.update(chunk)
        return h.hexdigest()

    def get_local_files(self):
        files = []
        for root,dirs,fnames in os.walk(CLOUD_DIR):
            for fname in fnames:
                fpath = os.path.join(root,fname)
                files.append({
                    "name": fname,
                    "path": fpath,
                    "size": os.path.getsize(fpath),
                    "hash": self.file_hash(fpath),
                    "mtime":os.path.getmtime(fpath),
                })
        return files

    def sync(self):
        if not self.server_ip:
            self.status = "No server configured"
            return
        self.syncing = True
        self.status  = "Syncing..."

        def run():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(10)
                s.connect((self.server_ip, CLOUD_PORT))

                local = self.get_local_files()
                manifest = json.dumps({
                    "action": "sync",
                    "device": socket.gethostname(),
                    "files" : [{
                        "name": f["name"],
                        "hash": f["hash"],
                        "size": f["size"]
                    } for f in local]
                })
                s.sendall(manifest.encode() + b"\n")

                resp = b""
                while b"\n" not in resp:
                    resp += s.recv(1)
                server_manifest = json.loads(resp.decode().strip())

                synced = 0
                for fname in server_manifest.get("need",[]):
                    lf = next((f for f in local if f["name"]==fname),None)
                    if lf:
                        with open(lf["path"],"rb") as f:
                            data = f.read()
                        header = json.dumps({
                            "action":"upload",
                            "name":fname,
                            "size":len(data)
                        })+"\n"
                        s.sendall(header.encode())
                        s.sendall(data)
                        synced += 1

                for fname in server_manifest.get("send",[]):
                    req = json.dumps({"action":"download","name":fname})+"\n"
                    s.sendall(req.encode())
                    resp2 = b""
                    while b"\n" not in resp2:
                        resp2 += s.recv(1)
                    finfo    = json.loads(resp2.decode().strip())
                    received = 0
                    fpath    = os.path.join(CLOUD_DIR, fname)
                    with open(fpath,"wb") as f:
                        while received < finfo["size"]:
                            chunk = s.recv(min(4096,finfo["size"]-received))
                            if not chunk:
                                break
                            f.write(chunk)
                            received += len(chunk)
                    synced += 1

                s.close()
                self.last_sync = time.strftime("%H:%M %d/%m")
                self.save_config()
                self.files   = self.get_local_files()
                self.status  = f"Synced {synced} files"
            except Exception as e:
                self.status = f"Sync error: {str(e)[:30]}"
            finally:
                self.syncing = False

        threading.Thread(target=run, daemon=True).start()

    def show(self):
        self.visible = True
        self.files   = self.get_local_files()

    def hide(self):
        self.visible = False

    def rr(self, color, rect, radius):
        x, y, w, h = rect
        r = min(radius, w//2, h//2)
        pygame.draw.rect(self.screen, color, (x+r, y, w-2*r, h))
        pygame.draw.rect(self.screen, color, (x, y+r, w, h-2*r))
        for cx, cy in [(x+r,y+r),(x+w-r,y+r),(x+r,y+h-r),(x+w-r,y+h-r)]:
            pygame.draw.circle(self.screen, color, (cx,cy), r)

    def draw(self):
        if not self.visible:
            return
        self.screen.fill(BG)
        pygame.draw.rect(self.screen,(22,22,28),(0,0,self.W,50))
        pygame.draw.line(self.screen,(50,50,60),(0,50),(self.W,50),1)

        title = self.font.render("Julius Cloud", True, WHITE)
        self.screen.blit(title,(self.W//2-title.get_width()//2,14))

        col  = GREEN if not self.syncing else PURPLE
        dots = "..."[:(int(time.time()*2)%4)] if self.syncing else ""
        st   = self.font_small.render(self.status+dots, True, col)
        self.screen.blit(st,(self.W//2-st.get_width()//2,36))

        # Server status
        self.rr(CARD,(8,58,self.W-16,48),10)
        srv = self.font_small.render(
            f"Server: {self.server_ip or 'Not configured'}", True, WHITE)
        ls  = self.font_small.render(
            f"Last sync: {self.last_sync}", True, DIM)
        self.screen.blit(srv,(16,66))
        self.screen.blit(ls,(16,84))

        sync_btn = self.font_small.render("Sync Now",True,WHITE)
        self.rr(BLUE,(self.W-90,63,80,36),10)
        self.screen.blit(sync_btn,
            (self.W-90+40-sync_btn.get_width()//2,
             63+18-sync_btn.get_height()//2))
        self.sync_btn_rect = (self.W-90,63,80,36)

        # Files
        files_title = self.font.render(
            f"Files ({len(self.files)})", True, WHITE)
        self.screen.blit(files_title,(12,116))
        pygame.draw.line(self.screen,(50,50,60),(0,134),(self.W,134),1)

        y = 138
        if not self.files:
            empty = self.font_small.render(
                "No files synced yet", True, DIM)
            self.screen.blit(empty,(12,y))
        else:
            for f in self.files[:6]:
                self.rr(CARD,(8,y,self.W-16,40),8)
                nm  = self.font_small.render(
                    f["name"][:24], True, WHITE)
                sz  = self.font_small.render(
                    f"{f['size']//1024}KB", True, DIM)
                self.screen.blit(nm,(16,y+6))
                self.screen.blit(sz,(self.W-sz.get_width()-16,y+6))
                y += 46

    def handle_touch(self, pos):
        if not self.visible:
            return
        if hasattr(self,"sync_btn_rect"):
            r = self.sync_btn_rect
            if r[0]<=pos[0]<=r[0]+r[2] and r[1]<=pos[1]<=r[1]+r[3]:
                self.sync()
