import pygame, math, random, json, os, sys
import numpy as np
import struct, wave, io
pygame.init()

# ══════════════════════════════════════════════════════════════════════════
# PROCEDURAL MUSIC — generated at startup, no external files needed
# Style: upbeat chiptune / electronic, fits Geometry Dash vibe
# ══════════════════════════════════════════════════════════════════════════
pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=1024)
SAMPLE_RATE = 44100

def _note(freq, dur, vol=0.4, wave_type='square', attack=0.01, release=0.05):
    """Generate one note as a numpy float32 array."""
    n = int(SAMPLE_RATE * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    if wave_type == 'square':
        w = np.sign(np.sin(2*np.pi*freq*t))
    elif wave_type == 'saw':
        w = 2*(t*freq - np.floor(t*freq + 0.5))
    elif wave_type == 'tri':
        w = 2*np.abs(2*(t*freq - np.floor(t*freq+0.5))) - 1
    else:  # sine
        w = np.sin(2*np.pi*freq*t)
    # envelope
    env = np.ones(n)
    atk = int(SAMPLE_RATE*attack)
    rel = int(SAMPLE_RATE*release)
    if atk > 0: env[:atk] = np.linspace(0,1,atk)
    if rel > 0 and rel < n: env[n-rel:] = np.linspace(1,0,rel)
    return (w * env * vol).astype(np.float32)

def _silence(dur):
    return np.zeros(int(SAMPLE_RATE*dur), dtype=np.float32)

# Note frequencies (Hz)
_NF = {
    'C3':130.81,'D3':146.83,'E3':164.81,'F3':174.61,'G3':196.00,'A3':220.00,'B3':246.94,
    'C4':261.63,'D4':293.66,'E4':329.63,'F4':349.23,'G4':392.00,'A4':440.00,'B4':493.88,
    'C5':523.25,'D5':587.33,'E5':659.25,'F5':698.46,'G5':783.99,'A5':880.00,'B5':987.77,
    'C6':1046.50,'D6':1174.66,'E6':1318.51,
    'Bb3':233.08,'Eb4':311.13,'Ab4':415.30,'Bb4':466.16,'Eb5':622.25,'Ab5':830.61,
}

def _n(name, dur, vol=0.35, wt='square'):
    return _note(_NF[name], dur, vol, wt)

def _build_track():
    """
    Build a ~60-second looping chiptune track.
    Structure: intro (8 bars) → verse (8 bars) → chorus (8 bars) → bridge (4 bars) → chorus (8 bars)
    BPM: 140  → quarter note = 0.4286s, eighth = 0.2143s, sixteenth = 0.1071s
    """
    Q  = 60/140          # quarter note
    E  = Q/2             # eighth
    S  = Q/4             # sixteenth
    H  = Q*2             # half

    def bar(*notes):
        """Concatenate note arrays into one bar."""
        return np.concatenate(notes)

    # ── MELODY LINE (square wave, lead) ──────────────────────────────────
    # Intro: simple ascending motif
    m_intro = np.concatenate([
        bar(_n('C5',E), _n('E5',E), _n('G5',E), _n('C6',E),
            _n('B5',E), _n('G5',E), _n('E5',E), _n('C5',E)),
        bar(_n('D5',E), _n('F5',E), _n('A5',E), _n('D6',E),
            _n('C6',E), _n('A5',E), _n('F5',E), _n('D5',E)),
        bar(_n('E5',E), _n('G5',E), _n('B5',E), _n('E6',E),
            _n('D6',E), _n('B5',E), _n('G5',E), _n('E5',E)),
        bar(_n('C5',Q), _n('G5',Q), _n('E5',H)),
    ] * 2)

    # Verse: rhythmic syncopated melody
    m_verse = np.concatenate([
        bar(_n('C5',S),_silence(S),_n('E5',S),_n('G5',S),
            _n('C6',E),_n('B5',S),_silence(S),
            _n('A5',S),_n('G5',S),_n('F5',E),_n('E5',E)),
        bar(_n('D5',S),_silence(S),_n('F5',S),_n('A5',S),
            _n('D6',E),_n('C6',S),_silence(S),
            _n('Bb4' if 'Bb4' in _NF else 'A4',S),_n('A4',S),_n('G4',E),_n('F4',E) if 'F4' in _NF else _n('E4',E)),
        bar(_n('E5',S),_silence(S),_n('G5',S),_n('B5',S),
            _n('E6',E),_n('D6',S),_silence(S),
            _n('C6',S),_n('B5',S),_n('A5',E),_n('G5',E)),
        bar(_n('C5',Q),_n('G4',E),_n('C5',E),_n('E5',Q),_n('G5',Q)),
    ] * 2)

    # Chorus: energetic, high register
    m_chorus = np.concatenate([
        bar(_n('C6',E),_n('B5',E),_n('A5',E),_n('G5',E),
            _n('F5',E),_n('E5',E),_n('D5',E),_n('C5',E)),
        bar(_n('D5',E),_n('E5',E),_n('F5',E),_n('G5',E),
            _n('A5',E),_n('B5',E),_n('C6',E),_n('D6',E)),
        bar(_n('E6',Q),_n('D6',E),_n('C6',E),_n('B5',Q),_n('A5',Q)),
        bar(_n('G5',H),_n('C6',H)),
    ] * 2)

    # Bridge: softer, different feel (tri wave)
    def _nt(name,dur,vol=0.25): return _note(_NF[name],dur,vol,'tri')
    m_bridge = np.concatenate([
        bar(_nt('G4',E),_nt('A4',E),_nt('B4',E),_nt('C5',E),
            _nt('D5',E),_nt('E5',E),_nt('F5',E),_nt('G5',E)),
        bar(_nt('G5',E),_nt('F5',E),_nt('E5',E),_nt('D5',E),
            _nt('C5',E),_nt('B4',E),_nt('A4',E),_nt('G4',E)),
        bar(_nt('C5',Q),_nt('E5',Q),_nt('G5',Q),_nt('C6',Q)),
        bar(_nt('B5',H),_nt('G5',H)),
    ])

    # ── BASS LINE (saw wave, low) ─────────────────────────────────────────
    def _b(name,dur,vol=0.25): return _note(_NF[name],dur,vol,'saw')

    bass_intro  = np.concatenate([
        bar(_b('C3',Q),_b('C3',Q),_b('G3',Q),_b('G3',Q)),
        bar(_b('D3',Q),_b('D3',Q),_b('A3',Q),_b('A3',Q)),
        bar(_b('E3',Q),_b('E3',Q),_b('B3',Q),_b('B3',Q)),
        bar(_b('C3',H),_b('G3',H)),
    ] * 2)

    bass_verse  = np.concatenate([
        bar(_b('C3',E),_b('C3',E),_b('G3',E),_b('E3',E),
            _b('C3',E),_b('G3',E),_b('E3',E),_b('C3',E)),
        bar(_b('D3',E),_b('D3',E),_b('A3',E),_b('F3',E),
            _b('D3',E),_b('A3',E),_b('F3',E),_b('D3',E)),
        bar(_b('E3',E),_b('E3',E),_b('B3',E),_b('G3',E),
            _b('E3',E),_b('B3',E),_b('G3',E),_b('E3',E)),
        bar(_b('C3',Q),_b('G3',Q),_b('C3',Q),_b('G3',Q)),
    ] * 2)

    bass_chorus = np.concatenate([
        bar(_b('C3',E),_b('E3',E),_b('G3',E),_b('C4',E),
            _b('G3',E),_b('E3',E),_b('C3',E),_b('G3',E)),
        bar(_b('D3',E),_b('F3',E),_b('A3',E),_b('D4',E),
            _b('A3',E),_b('F3',E),_b('D3',E),_b('A3',E)),
        bar(_b('E3',Q),_b('B3',Q),_b('E3',Q),_b('B3',Q)),
        bar(_b('C3',H),_b('G3',H)),
    ] * 2)

    bass_bridge = np.concatenate([
        bar(_b('G3',Q),_b('G3',Q),_b('D3',Q),_b('D3',Q)),
        bar(_b('G3',Q),_b('D3',Q),_b('G3',Q),_b('D3',Q)),
        bar(_b('C3',Q),_b('G3',Q),_b('E3',Q),_b('C3',Q)),
        bar(_b('G3',H),_b('C3',H)),
    ])

    # ── MIX melody + bass ────────────────────────────────────────────────
    def mix(a, b):
        n = max(len(a),len(b))
        out = np.zeros(n, dtype=np.float32)
        out[:len(a)] += a
        out[:len(b)] += b
        return np.clip(out, -1.0, 1.0)

    track = np.concatenate([
        mix(m_intro,  bass_intro),
        mix(m_verse,  bass_verse),
        mix(m_chorus, bass_chorus),
        mix(m_bridge, bass_bridge),
        mix(m_chorus, bass_chorus),
    ])

    # normalise
    peak = np.max(np.abs(track))
    if peak > 0: track = track / peak * 0.85

    # convert to int16 for pygame
    return (track * 32767).astype(np.int16)

# Build and start music
print("Generating music...")
_track_data = _build_track()
_music_sound = pygame.sndarray.make_sound(np.ascontiguousarray(_track_data))
_music_sound.set_volume(0.55)
_music_sound.play(loops=-1)   # loop forever
print("Music started.")


WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Geometry Dash — Stereo Madness")
clock  = pygame.time.Clock()
FPS    = 60

# ── core constants ────────────────────────────────────────────────────────
SPEED    = 7
GRAVITY  = 1.4
JUMP_VEL = -17
GROUND_Y = 480      # y-coord of the top of the floor
TILE     = 44
PW, PH   = 38, 38   # player hitbox

CEIL_Y   = 44       # y-coord of the ceiling top edge when gravity is flipped

FONT    = pygame.font.SysFont("Courier New", 13, bold=True)
FONT_LG = pygame.font.SysFont("Courier New", 28, bold=True)
FONT_XL = pygame.font.SysFont("Courier New", 40, bold=True)

C_MAIN  = (0, 255, 204)
C_WIN   = (0, 255, 136)
C_DEATH = (255, 68,  68)
C_BG1   = (5,   5,  24)
C_BG2   = (13, 13,  46)
C_PLAT  = (255, 200,  50)
C_SAW   = (255,  80,  80)
C_GRAV  = (180,  80, 255)

# ── save ──────────────────────────────────────────────────────────────────
SAVE_FILE = "gd_save.json"
def load_save():
    try:
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE) as f: return json.load(f)
    except: pass
    return {}
def write_save(d):
    try:
        with open(SAVE_FILE,"w") as f: json.dump(d,f)
    except: pass
saves = load_save()

# ── background colour palette — changes as level progresses ───────────────
# Each entry: (top_colour, bottom_colour, ground_line_colour)
# Interpolated smoothly based on % completion
BG_PALETTE = [
    ((5,   5,  24), (13,  13,  46), (0, 160, 130)),   #  0%  deep navy
    ((10,   0,  40), (30,   5,  60), (120, 60, 200)),  # 14%  deep purple
    ((0,   15,  40), (0,   40,  80), (0, 180, 220)),   # 28%  ocean blue
    ((0,   30,  20), (0,   60,  30), (0, 220, 100)),   # 42%  dark green
    ((40,  10,   0), (80,  20,   0), (255, 140, 0)),   # 57%  ember orange
    ((30,   0,  40), (60,   0,  80), (200, 80, 255)),  # 71%  violet
    ((40,   0,  20), (80,   0,  30), (255, 60, 120)),  # 85%  crimson
    ((5,   5,  24), (13,  13,  46), (0, 200, 180)),   # 100% back to dark (finish)
]

def _lerp(a, b, t):
    return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))

def get_bg_colours(pct):
    """Interpolate smoothly between palette entries based on 0-1 progress."""
    p = len(BG_PALETTE)-1
    scaled = pct*p
    idx = int(scaled)
    t = scaled-idx
    if idx >= p: return BG_PALETTE[-1]
    top  = _lerp(BG_PALETTE[idx][0], BG_PALETTE[idx+1][0], t)
    bot  = _lerp(BG_PALETTE[idx][1], BG_PALETTE[idx+1][1], t)
    line = _lerp(BG_PALETTE[idx][2], BG_PALETTE[idx+1][2], t)
    return top, bot, line

# cached gradient surface — redrawn when colour changes enough
_grad_cache = {"surf": None, "top": None, "bot": None}

def get_grad(top, bot):
    if _grad_cache["top"]==top and _grad_cache["bot"]==bot:
        return _grad_cache["surf"]
    surf = pygame.Surface((WIDTH, HEIGHT))
    for i in range(HEIGHT):
        f = i/HEIGHT
        c = _lerp(top, bot, f)
        pygame.draw.line(surf, c, (0,i), (WIDTH,i))
    _grad_cache.update({"surf":surf,"top":top,"bot":bot})
    return surf



# ── Particle ──────────────────────────────────────────────────────────────
class Particle:
    def __init__(self,x,y,col):
        a=random.uniform(0,math.pi*2); sp=random.uniform(3,9)
        self.x=x; self.y=y
        self.vx=math.cos(a)*sp; self.vy=math.sin(a)*sp-3
        self.life=1.0; self.col=col
        self.sz=random.uniform(3,9)
        self.rot=random.uniform(0,math.pi*2); self.rv=random.uniform(-0.3,0.3)
    def update(self):
        self.x+=self.vx; self.y+=self.vy; self.vy+=0.2
        self.life-=0.04; self.rot+=self.rv
    def draw(self,surf,cx):
        if self.life<=0: return
        alpha=max(0,min(255,int(self.life*255))); sz=max(1,int(self.sz))
        s=pygame.Surface((sz*2,sz*2),pygame.SRCALPHA)
        r,g,b=self.col
        pygame.draw.rect(s,(r,g,b,alpha),(0,0,sz*2,sz*2))
        rot=pygame.transform.rotate(s,math.degrees(self.rot))
        surf.blit(rot,(self.x-cx-rot.get_width()//2,
                       self.y-rot.get_height()//2))

# ═══════════════════════════════════════════════════════════════════════════
# LEVEL BUILDER
# Item list (everything we can place):
#  1. flat(n)               – n ground tiles, no hazard
#  2. spike(n)              – n ground spikes side by side
#  3. block(h)              – 1 column, h tiles tall (side = death)
#  4. staircase()           – 1→2→3 ascending columns, gap=3 between each
#  5. platform(n_sp,sx)     – floating platform over middle of n_sp spikes
#  6. plat_stair(sx,n_sp)   – 3 ascending platforms over a wide spike zone
#  7. elevated_floor(n)     – long raised floor (reached via staircase)
#  8. sawblade(y_off)       – spinning lethal circle, y_off<0 raises it
#  9. gravity_portal()      – flips gravity; second call flips back
# 10. ceil_flat(n)          – flat ceiling tiles (safe, used after flip)
# 11. ceil_spike(n)         – ceiling spikes (lethal, used during flip)
# ═══════════════════════════════════════════════════════════════════════════

VIS_I  = 8    # spike visual inset
HIT_I  = 13   # spike hitbox inset (narrower for fairness)
SP_TOP = 8    # spike tip offset from tile top

FLOOR_Y   = GROUND_Y - TILE*3      # elevated floor y (top of 3-tall block)
PLAT_LOW  = GROUND_Y - TILE*2 - 4  # low floating platform (over 1-2 spikes)
PLAT_MID  = GROUND_Y - TILE*3 - 4  # mid floating platform
PLAT_HIGH = GROUND_Y - TILE*4 - 4  # high floating platform (platform stairs top)

def make_level():
    GT=[]   # ground tiles   — top-land only, no side kill
    BT=[]   # block tiles    — full collision, side = death
    ST=[]   # spike tiles    — lethal AABB
    PT=[]   # floating plats — top-land only, pass-through from below
    FT=[]   # elevated floor — full collision like blocks
    SAW=[]  # sawblades      — lethal circle
    GRAV=[] # gravity portals
    x=0

    # ── internal helpers ─────────────────────────────────────────────────

    def _ground(gx, gy=GROUND_Y):
        GT.append({"x":gx,"y":gy,"w":TILE,"h":HEIGHT})

    def _spike(gx, gy, flipped=False):
        """Place one spike. flipped=True → ceiling spike (tip points down)."""
        if not flipped:
            ST.append({
                "vx":gx,"vy":gy-TILE,"vw":TILE,"vh":TILE,
                "vi":VIS_I,"vto":SP_TOP,
                "x":gx+HIT_I,"y":gy-TILE+SP_TOP+4,
                "w":TILE-HIT_I*2,"h":TILE-SP_TOP-8,
                "ceil":False,
            })
        else:
            # ceiling spike hangs at CEIL_Y, tip points downward
            ST.append({
                "vx":gx,"vy":CEIL_Y,"vw":TILE,"vh":TILE,
                "vi":VIS_I,"vto":SP_TOP,
                "x":gx+HIT_I,"y":CEIL_Y+4,
                "w":TILE-HIT_I*2,"h":TILE-SP_TOP-4,
                "ceil":True,
            })

    # ── public builders ──────────────────────────────────────────────────

    def flat(n):
        nonlocal x
        for _ in range(n):
            _ground(x); x+=TILE

    def spike(n):
        nonlocal x
        for _ in range(n):
            _ground(x); _spike(x, GROUND_Y); x+=TILE

    def block(h=1):
        nonlocal x
        _ground(x)
        for j in range(h):
            BT.append({"x":x,"y":GROUND_Y-TILE*(j+1),"w":TILE,"h":TILE})
        x+=TILE

    def staircase(gap=3):
        """Ascending 1→2→3 staircase. Hold jump to climb cleanly."""
        for i,h in enumerate([1,2,3]):
            block(h)
            if i<2: flat(gap)

    def platform(n_sp, sx):
        """
        One floating platform centred over the MIDDLE spike(s) of a group.
        n_sp=2 → 1 tile over centre
        n_sp=3 → 1 tile over middle spike
        n_sp=4 → 2 tiles over middle two spikes
        """
        if n_sp<=2:
            mid=sx+(n_sp*TILE)//2-TILE//2
            PT.append({"x":mid,"y":PLAT_LOW,"w":TILE,"h":10})
        elif n_sp==3:
            PT.append({"x":sx+TILE,"y":PLAT_LOW,"w":TILE,"h":10})
        else:
            PT.append({"x":sx+TILE,   "y":PLAT_LOW,"w":TILE,"h":10})
            PT.append({"x":sx+TILE*2, "y":PLAT_LOW,"w":TILE,"h":10})

    def plat_stair(sx, n_sp):
        """
        Platform staircase: 3 platforms at ascending heights spanning a wide
        spike zone. Player jumps from ground → low plat → mid plat → high plat
        → back to ground on the other side.
        sx      = x where the spike zone starts
        n_sp    = total number of spike tiles in the zone (should be 8-10)
        Heights: low → mid → high, each separated by ~2 tiles horizontally.
        """
        seg = (n_sp*TILE)//3
        PT.append({"x":sx,         "y":PLAT_LOW,  "w":TILE*2,"h":10})
        PT.append({"x":sx+seg,     "y":PLAT_MID,  "w":TILE*2,"h":10})
        PT.append({"x":sx+seg*2,   "y":PLAT_HIGH, "w":TILE*2,"h":10})

    def elevated_floor(n):
        """Long raised floor at FLOOR_Y. Reach via staircase."""
        nonlocal x
        for _ in range(n):
            FT.append({"x":x,"y":FLOOR_Y,"w":TILE,"h":TILE})
            _ground(x)
            x+=TILE

    def sawblade(y_off=0):
        """
        Spinning lethal sawblade.
        y_off=0  → sits on the ground
        y_off<0  → floats (negative = higher up, e.g. -TILE floats one tile up)
        """
        nonlocal x
        _ground(x)
        cy = GROUND_Y - TILE//2 + y_off
        SAW.append({"x":x+TILE//2,"y":cy,"r":TILE//2-4,"rot":0.0})
        x+=TILE

    def gravity_portal():
        """
        Purple gate. Player walks through → gravity flips.
        Safe rule: the caller must ensure flat ground for 4 tiles BEFORE
        this call, and flat ceiling for 3 tiles AFTER (handled in layout).
        """
        nonlocal x
        # portal is drawn but not solid — player passes through
        GRAV.append({"x":x+TILE//2,"y":GROUND_Y-TILE*4,
                     "w":12,"h":TILE*4,"triggered":False})
        _ground(x)   # keep ground under portal so player doesn't fall
        x+=TILE

    def ceil_flat(n):
        """
        During gravity flip the player runs along the ceiling.
        We don't need tiles here — the ceiling is a hard boundary at CEIL_Y.
        This just advances x and places ground tiles below so the visual
        looks complete if we flip back.
        """
        nonlocal x
        for _ in range(n):
            _ground(x); x+=TILE

    def ceil_spike(n):
        """Ceiling spikes during gravity flip (tip points downward)."""
        nonlocal x
        for _ in range(n):
            _ground(x)
            _spike(x, GROUND_Y, flipped=True)
            x+=TILE

    # ══════════════════════════════════════════════════════════════════════
    # THE LEVEL — 10 sections, ~105 tiles each ≈ 110 seconds total
    #
    # Design philosophy:
    #  • Every section introduces or combines 1-2 ideas
    #  • Gravity flips always land on safe ground/ceiling, hazards start
    #    only after 3 buffer tiles
    #  • Platform stairs span wide spike zones so they feel rewarding
    #  • Difficulty ramps: S1 gentle → S5-S6 first big challenge →
    #    S9 hardest → S10 finale with breathing room at the end
    # ══════════════════════════════════════════════════════════════════════

    # ── S1 (0-10%): Energetic opening with floating platform staircase ──────
    # 2-second safe runway before first hazard (2s × 9.5 tiles/s ≈ 19 tiles)
    flat(19)

    # Floating platform staircase intro:
    # Each platform is one step higher, spaced so a jump carries you up.
    # Spikes underneath each gap so missing a platform is lethal.
    sx=x
    spike(2)                            # gap 1 under lowest platform
    PT.append({"x":sx,"y":PLAT_LOW,"w":TILE*2,"h":10})
    spike(2)                            # gap 2 under mid platform
    PT.append({"x":x-TILE,"y":PLAT_MID,"w":TILE*2,"h":10})
    spike(2)                            # gap 3 under high platform
    PT.append({"x":x-TILE,"y":PLAT_HIGH,"w":TILE*2,"h":10})
    flat(6)

    # Back to ground level — first block and spike rhythm
    spike(1); flat(6)
    block(1); flat(6)
    spike(1); flat(6)
    # second floating platform staircase (same pattern, player now expects it)
    sx=x
    spike(2)
    PT.append({"x":sx,"y":PLAT_LOW,"w":TILE*2,"h":10})
    spike(2)
    PT.append({"x":x-TILE,"y":PLAT_MID,"w":TILE*2,"h":10})
    spike(2)
    PT.append({"x":x-TILE,"y":PLAT_HIGH,"w":TILE*2,"h":10})
    flat(6)
    spike(1); flat(8)                   # end of S1

    # ── S2 (10-20%): Doubles, first sawblade, first floating platform ──────
    sx=x; spike(2); platform(2,sx); flat(8)
    block(1); flat(6)
    spike(1); flat(6)
    sawblade(); flat(8)                 # first sawblade — player sees it coming
    sx=x; spike(2); platform(2,sx); flat(8)
    spike(1); flat(6)
    block(2); flat(8)                   # two-tall block, must jump earlier
    sx=x; spike(2); platform(2,sx); flat(8)
    spike(1); flat(8)

    # ── S3 (20-30%): Triples, block(2), sawblade, staircase intro ──────────
    sx=x; spike(3); platform(3,sx); flat(8)
    block(1); flat(6)
    spike(1); flat(6)
    sx=x; spike(2); platform(2,sx); flat(6)
    sawblade(); flat(6)
    block(2); flat(6)
    sx=x; spike(3); platform(3,sx); flat(8)
    spike(1); flat(6)
    # STAIRCASE 1 — taught here for the first time, no hazard after
    flat(4); staircase(gap=3); flat(10)

    # ── S4 (30-40%): Elevated floor via staircase, spike on floor ──────────
    spike(1); flat(6)
    sx=x; spike(2); platform(2,sx); flat(6)
    sawblade(); flat(4)
    # staircase leads to elevated floor
    flat(4); staircase(gap=3)
    elevated_floor(8)
    # place one spike ON the elevated floor to force a jump off
    ST.append({
        "vx":x-TILE*3,"vy":FLOOR_Y-TILE,
        "vw":TILE,"vh":TILE,"vi":VIS_I,"vto":SP_TOP,
        "x":x-TILE*3+HIT_I,"y":FLOOR_Y-TILE+SP_TOP+4,
        "w":TILE-HIT_I*2,"h":TILE-SP_TOP-8,"ceil":False,
    })
    flat(8)
    spike(1); flat(6)
    block(1); flat(8)

    # ── S5 (40-50%): PLATFORM STAIRS — cross a wide spike zone ─────────────
    spike(1); flat(6)
    # wide spike zone (9 spikes) with ascending platform staircase above
    sx=x
    spike(9)
    plat_stair(sx, 9)
    flat(8)
    sawblade(y_off=-TILE//2); flat(6)  # floating saw (jump over it)
    sx=x; spike(3); platform(3,sx); flat(6)
    spike(1); flat(6)
    sx=x; spike(4); platform(4,sx); flat(8)
    block(1); flat(6)

    # ── S6 (50-60%): GRAVITY FLIP 1 — safe design ─────────────────────────
    # Pre-flip: land player on flat ground, then portal
    spike(1); flat(6)
    sx=x; spike(2); platform(2,sx); flat(8)
    # 4 flat tiles then portal
    flat(4)
    gravity_portal()                    # FLIP — now falls toward ceiling
    # 28 safe ceiling tiles (~3 seconds) before ANY ceiling spike appears
    # This gives the player time to orient and understand the flip
    ceil_flat(28)
    # ceiling spikes now start — single spikes with generous 4-tile gaps
    ceil_spike(1); ceil_flat(4)
    ceil_spike(1); ceil_flat(4)
    ceil_spike(1); ceil_flat(4)
    # 4 safe tiles then return portal
    ceil_flat(4)
    gravity_portal()                    # FLIP BACK — now falls toward ground
    # 6 safe flat tiles after flip before any hazard
    flat(6)
    spike(1); flat(6)
    block(1); flat(8)

    # ── S7 (60-70%): Intensity — quads, block(2), sawblade, staircase 2 ────
    sx=x; spike(3); platform(3,sx); flat(8)
    sawblade(); flat(6)
    sx=x; spike(4); platform(4,sx); flat(8)
    block(2); flat(6)
    spike(1); flat(6)
    sawblade(); flat(6)
    sx=x; spike(2); platform(2,sx); flat(6)
    spike(1); flat(6)
    # STAIRCASE 2 — player knows this now, spike right after the jump-off
    flat(4); staircase(gap=3); flat(4)
    spike(1); flat(8)
    # ELEVATED FLOOR 2 — reached from staircase, longer this time
    flat(4); staircase(gap=3)
    elevated_floor(10)
    # two spikes on the floor so player must jump twice across the floor
    ST.append({
        "vx":x-TILE*5,"vy":FLOOR_Y-TILE,
        "vw":TILE,"vh":TILE,"vi":VIS_I,"vto":SP_TOP,
        "x":x-TILE*5+HIT_I,"y":FLOOR_Y-TILE+SP_TOP+4,
        "w":TILE-HIT_I*2,"h":TILE-SP_TOP-8,"ceil":False,
    })
    ST.append({
        "vx":x-TILE*2,"vy":FLOOR_Y-TILE,
        "vw":TILE,"vh":TILE,"vi":VIS_I,"vto":SP_TOP,
        "x":x-TILE*2+HIT_I,"y":FLOOR_Y-TILE+SP_TOP+4,
        "w":TILE-HIT_I*2,"h":TILE-SP_TOP-8,"ceil":False,
    })
    flat(8)

    # ── S8 (70-80%): Platform stairs HARDER, mixed hazards ─────────────────
    spike(1); flat(6)
    sawblade(y_off=-TILE); flat(6)     # higher floating saw, must jump OVER
    sx=x; spike(2); platform(2,sx); flat(6)
    # second platform staircase — wider zone (10 spikes)
    sx=x
    spike(10)
    plat_stair(sx, 10)
    flat(6)
    sawblade(); flat(6)
    sx=x; spike(3); platform(3,sx); flat(6)
    block(2); flat(6)
    spike(1); flat(6)
    sx=x; spike(4); platform(4,sx); flat(8)

    # ── S9 (80-90%): GRAVITY FLIP 2 — harder, more ceiling spikes ──────────
    spike(1); flat(6)
    sx=x; spike(2); platform(2,sx); flat(6)
    sawblade(); flat(6)
    flat(4)
    gravity_portal()                    # FLIP
    # 28 safe ceiling tiles (~3 seconds) before ceiling spikes
    ceil_flat(28)
    # harder pattern: single then double spikes, bigger gaps than flip 1
    ceil_spike(1); ceil_flat(4)
    ceil_spike(2); ceil_flat(5)         # double spike — extra wide gap
    ceil_spike(1); ceil_flat(4)
    ceil_spike(1); ceil_flat(4)
    # 4 safe tiles then return portal
    ceil_flat(4)
    gravity_portal()                    # FLIP BACK
    flat(6)                             # 6 safe tiles
    spike(1); flat(6)
    block(1); flat(6)

    # ── S10 (90-100%): Finale — everything together, then cool-down ─────────
    sx=x; spike(3); platform(3,sx); flat(6)
    sawblade(); flat(6)
    sx=x; spike(4); platform(4,sx); flat(6)
    block(2); flat(6)
    sawblade(y_off=-TILE//2); flat(6)
    spike(1); flat(6)
    sx=x; spike(2); platform(2,sx); flat(6)
    spike(1); flat(6)
    sawblade(); flat(6)
    sx=x; spike(3); platform(3,sx); flat(6)
    block(1); flat(6)
    spike(1); flat(8)
    # final wide spike zone with platform staircase
    sx=x
    spike(9)
    plat_stair(sx, 9)
    flat(6)
    spike(1); flat(8)
    # long cool-down runway to the finish line
    flat(24)

    # ── End gate ─────────────────────────────────────────────────────────
    total_w = x + TILE*10
    eg_x    = x + TILE*6
    for _ in range(10):
        _ground(x); x+=TILE
    endgate = {"x":eg_x,"y":GROUND_Y-TILE*5,"w":10,"h":TILE*5}

    return GT,BT,ST,PT,FT,SAW,GRAV,endgate,total_w


# ── game state ────────────────────────────────────────────────────────────
state="menu"; attempt=0; player={}
GT=[]; BT=[]; ST=[]; PT=[]; FT=[]; SAW=[]; GRAV=[]; EG={}; total_w=0
cam_x=0.0; frame=0; score=0; air_rot=0.0
grav_flipped=False
particles=[]; message=""; msg_timer=0

def start_game():
    global state,player,GT,BT,ST,PT,FT,SAW,GRAV,EG,total_w
    global cam_x,frame,score,air_rot,particles,attempt,msg_timer,grav_flipped
    attempt+=1
    GT,BT,ST,PT,FT,SAW,GRAV,EG,total_w = make_level()
    player={"x":80.0,"y":float(GROUND_Y-TILE),"w":PW,"h":PH,
            "vy":0.0,"on_ground":False,"dead":False}
    cam_x=0.0; frame=0; score=0; air_rot=0.0
    grav_flipped=False; particles=[]; msg_timer=0
    state="playing"

def spawn_p(x,y,col,n=18):
    for _ in range(n): particles.append(Particle(x,y,col))

def die():
    global state,message,msg_timer
    if player["dead"]: return
    player["dead"]=True
    spawn_p(player["x"]+PW//2,player["y"]+PH//2,C_MAIN,22)
    pct=max(0,min(100,int(cam_x/max(1,total_w-WIDTH)*100)))
    message=f"{pct}%  ·  attempt {attempt}"
    msg_timer=55; state="dead"

def win_game():
    global state
    if state=="win": return
    state="win"
    if not saves.get("best") or score>saves["best"]:
        saves["best"]=score; saves["attempts"]=attempt; write_save(saves)
    spawn_p(WIDTH//2,HEIGHT//2,C_WIN,55)

# ── jump system ───────────────────────────────────────────────────────────
jump_held=False

def try_jump():
    if state in("win","menu","dead"): return
    if not jump_held: return
    if state=="playing" and not player["dead"] and player["on_ground"]:
        player["vy"] = -JUMP_VEL if grav_flipped else JUMP_VEL
        player["on_ground"]=False

def do_jump():
    global jump_held,state
    jump_held=True
    if state=="dead": return
    if state in("win","menu"): start_game(); return

# ── collision helpers ─────────────────────────────────────────────────────
def aabb(ax,ay,aw,ah,bx,by,bw,bh):
    return ax<bx+bw and ax+aw>bx and ay<by+bh and ay+ah>by

SIDE_THR=6

def collide_solid(t):
    """
    Resolve player vs a solid tile (block or elevated floor).
    Returns 'land', 'bonk', 'side', or None.
    Velocity-first priority: always resolve vertically before laterally.
    """
    if not aabb(player["x"],player["y"],player["w"],player["h"],
                t["x"],t["y"],t["w"],t["h"]): return None
    px,py=player["x"],player["y"]; pw,ph=player["w"],player["h"]
    tx,ty,tw,th=t["x"],t["y"],t["w"],t["h"]
    ol=(px+pw)-tx; or_=(tx+tw)-px
    ot=(py+ph)-ty; ob=(ty+th)-py
    horiz=min(ol,or_); vert=min(ot,ob)

    if not grav_flipped:
        # normal gravity: land on top, bonk on bottom, side only if tiny horiz
        if player["vy"]>=0 and ot>0 and ot<=vert+4:
            player["y"]=ty-ph; player["vy"]=0.0
            player["on_ground"]=True; return "land"
        if player["vy"]<0 and ob>0 and ob<=vert+4:
            player["y"]=ty+th; player["vy"]=0.0; return "bonk"
    else:
        # flipped gravity: land on bottom face of tile (player is upside down)
        if player["vy"]<=0 and ob>0 and ob<=vert+4:
            player["y"]=ty+th-ph; player["vy"]=0.0
            player["on_ground"]=True; return "land"
        if player["vy"]>0 and ot>0 and ot<=vert+4:
            player["y"]=ty-ph; player["vy"]=0.0; return "bonk"

    if horiz<=SIDE_THR: return "side"
    # edge-case large overlap: treat as landing
    if (not grav_flipped and player["vy"]>=0) or \
       (grav_flipped and player["vy"]<=0):
        if not grav_flipped:
            player["y"]=ty-ph
        else:
            player["y"]=ty+th-ph
        player["vy"]=0.0; player["on_ground"]=True; return "land"
    return None

# ── update ────────────────────────────────────────────────────────────────
def update():
    global cam_x,frame,score,air_rot,state,msg_timer,grav_flipped

    for p in particles: p.update()
    particles[:]=[p for p in particles if p.life>0]
    for s in SAW: s["rot"]=(s["rot"]+3.5)%360

    if state=="dead":
        msg_timer-=1
        if msg_timer<=0: start_game()
        return
    if state!="playing" or player["dead"]: return

    frame+=1; score=int(frame*SPEED*0.15)

    grav = -GRAVITY if grav_flipped else GRAVITY
    player["vy"]+=grav
    player["y"] +=player["vy"]
    player["x"] +=SPEED
    cam_x=max(0.0,player["x"]-130)
    px,py=player["x"],player["y"]; pw,ph=player["w"],player["h"]
    player["on_ground"]=False

    if px+pw>EG["x"]: win_game(); return

    # gravity portals — trigger when player centre crosses portal x
    pcx=px+pw/2
    for g in GRAV:
        if not g["triggered"] and abs(pcx-g["x"])<SPEED+6:
            g["triggered"]=True
            grav_flipped=not grav_flipped
            # soften velocity so player doesn't rocket away
            player["vy"]*=-0.3

    # spikes — lethal on narrow hitbox
    for t in ST:
        if aabb(px,py,pw,ph,t["x"],t["y"],t["w"],t["h"]): die(); return

    # sawblades — circle vs AABB closest-point test
    for s in SAW:
        cx,cy,r=s["x"],s["y"],s["r"]
        cpx=max(px,min(cx,px+pw)); cpy=max(py,min(cy,py+ph))
        if math.hypot(cpx-cx,cpy-cy)<r-2: die(); return

    # ground tiles — vertical only, never side-kill
    for t in GT:
        if not aabb(px,py,pw,ph,t["x"],t["y"],t["w"],t["h"]): continue
        ot=(py+ph)-t["y"]; ob=(t["y"]+t["h"])-py
        if not grav_flipped:
            if ot<=ob and player["vy"]>=0:
                player["y"]=t["y"]-ph; player["vy"]=0.0
                player["on_ground"]=True; py=player["y"]
            elif ob<ot and player["vy"]<0:
                player["y"]=t["y"]+t["h"]; player["vy"]=0.0; py=player["y"]
        else:
            if ob<=ot and player["vy"]<=0:
                player["y"]=t["y"]+t["h"]; player["vy"]=0.0
                player["on_ground"]=True; py=player["y"]

    # hard ceiling boundary during gravity flip
    if grav_flipped:
        if player["y"]<=CEIL_Y:
            player["y"]=float(CEIL_Y)
            player["vy"]=0.0; player["on_ground"]=True
            py=player["y"]

    # blocks — vertical-first, side = death
    for t in BT:
        res=collide_solid(t)
        if res=="side": die(); return
        if res in("land","bonk"): py=player["y"]

    # floating platforms — top-land only, pass-through from below
    for t in PT:
        if not aabb(px,py,pw,ph,t["x"],t["y"],t["w"],t["h"]): continue
        ot=(py+ph)-t["y"]
        if not grav_flipped:
            if 0<ot<20 and player["vy"]>=0:
                player["y"]=t["y"]-ph; player["vy"]=0.0
                player["on_ground"]=True; py=player["y"]
        else:
            # during flip, platforms act as ceiling (land on underside)
            ob=(t["y"]+t["h"])-py
            if 0<ob<20 and player["vy"]<=0:
                player["y"]=t["y"]+t["h"]; player["vy"]=0.0
                player["on_ground"]=True; py=player["y"]

    # elevated floor — full solid collision
    for t in FT:
        res=collide_solid(t)
        if res=="side": die(); return
        if res in("land","bonk"): py=player["y"]

    # out-of-bounds death
    if not grav_flipped and player["y"]>GROUND_Y+TILE*3: die(); return
    if player["y"]<-TILE*6: die(); return

    try_jump()
    if player["on_ground"]: air_rot=0.0
    else: air_rot+=(-0.09 if grav_flipped else 0.09)

# ── drawing ───────────────────────────────────────────────────────────────
def draw_bg():
    # solid colour gradient background that shifts as level progresses
    pct = max(0.0,min(1.0,cam_x/max(1,total_w-WIDTH))) if total_w>WIDTH else 0.0
    top, bot, line_col = get_bg_colours(pct)
    # fill entire screen with top colour first, then draw gradient
    screen.fill(top)
    # draw a smooth top-to-bottom gradient (top colour → bottom colour)
    for i in range(0, HEIGHT, 2):
        f = i / HEIGHT
        c = _lerp(top, bot, f)
        pygame.draw.line(screen, c, (0, i), (WIDTH, i))
        pygame.draw.line(screen, c, (0, i+1), (WIDTH, i+1))

    # ground line
    pygame.draw.line(screen, line_col, (0, GROUND_Y), (WIDTH, GROUND_Y), 2)

    if grav_flipped:
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((60, 0, 80, 50))
        screen.blit(ov, (0, 0))
        pygame.draw.line(screen, (180,80,255), (0,CEIL_Y+PH), (WIDTH,CEIL_Y+PH), 1)

def draw_tiles():
    ox=-cam_x

    # Ground
    for t in GT:
        tx=int(t["x"]+ox)
        if tx>WIDTH+TILE or tx<-TILE*2: continue
        s=pygame.Surface((t["w"],min(HEIGHT,HEIGHT-int(t["y"]))),pygame.SRCALPHA)
        s.fill((0,255,204,18)); screen.blit(s,(tx,int(t["y"])))
        pygame.draw.line(screen,(0,200,160),
            (tx,int(t["y"])),(tx+t["w"],int(t["y"])),2)

    # Blocks
    for t in BT:
        tx=int(t["x"]+ox)
        if tx>WIDTH+TILE or tx<-TILE*2: continue
        ty,tw,th=int(t["y"]),t["w"],t["h"]
        s=pygame.Surface((tw,th),pygame.SRCALPHA); s.fill((0,255,204,70))
        screen.blit(s,(tx,ty))
        pygame.draw.rect(screen,C_MAIN,(tx,ty,tw,th),2)
        inn=pygame.Surface((tw-10,th-10),pygame.SRCALPHA)
        inn.fill((0,255,204,100)); screen.blit(inn,(tx+5,ty+5))

    # Spikes (ground and ceiling)
    for t in ST:
        tx=int(t["vx"]+ox)
        if tx>WIDTH+TILE or tx<-TILE*2: continue
        vy=int(t["vy"]); vi=t["vi"]; vw=t["vw"]; vh=t["vh"]; vto=t["vto"]
        if not t["ceil"]:
            pts=[(tx+vw//2, vy+vto+2),(tx+vw-vi, vy+vh),(tx+vi, vy+vh)]
        else:
            # upside-down: tip points DOWN from ceiling
            pts=[(tx+vw//2, vy+vh-vto-2),(tx+vw-vi, vy),(tx+vi, vy)]
        pygame.draw.polygon(screen,C_MAIN,pts)
        g=pygame.Surface((vw+10,vh+10),pygame.SRCALPHA)
        gpts=[(p[0]-tx+5,p[1]-vy+5) for p in pts]
        pygame.draw.polygon(g,(0,255,204,22),gpts)
        screen.blit(g,(tx-5,vy-5))

    # Floating platforms
    for t in PT:
        tx=int(t["x"]+ox)
        if tx>WIDTH+TILE or tx<-TILE*2: continue
        ty,tw,th=int(t["y"]),t["w"],t["h"]
        pygame.draw.rect(screen,C_PLAT,(tx,ty,tw,th))
        g=pygame.Surface((tw,22),pygame.SRCALPHA)
        g.fill((255,200,50,25)); screen.blit(g,(tx,ty-6))

    # Elevated floor
    for t in FT:
        tx=int(t["x"]+ox)
        if tx>WIDTH+TILE or tx<-TILE*2: continue
        ty,tw,th=int(t["y"]),t["w"],t["h"]
        s=pygame.Surface((tw,th),pygame.SRCALPHA); s.fill((255,180,0,75))
        screen.blit(s,(tx,ty))
        pygame.draw.rect(screen,(255,200,50),(tx,ty,tw,th),2)
        pygame.draw.line(screen,(255,230,80),(tx,ty),(tx+tw,ty),3)
        fill=pygame.Surface((tw,max(1,GROUND_Y-ty-th)),pygame.SRCALPHA)
        fill.fill((255,140,0,12)); screen.blit(fill,(tx,ty+th))

    # Sawblades
    for s in SAW:
        sx=int(s["x"]-cam_x); sy=int(s["y"]); r=s["r"]
        if sx>WIDTH+TILE*2 or sx<-TILE*2: continue
        pygame.draw.circle(screen,C_SAW,(sx,sy),r,2)
        for i in range(8):
            a=math.radians(s["rot"]+i*45)
            x1=sx+int((r-5)*math.cos(a)); y1=sy+int((r-5)*math.sin(a))
            x2=sx+int((r+5)*math.cos(a)); y2=sy+int((r+5)*math.sin(a))
            pygame.draw.line(screen,C_SAW,(x1,y1),(x2,y2),2)
        pygame.draw.line(screen,(255,120,120),
            (sx-r//2,sy-r//2),(sx+r//2,sy+r//2),2)
        pygame.draw.line(screen,(255,120,120),
            (sx+r//2,sy-r//2),(sx-r//2,sy+r//2),2)
        gs=pygame.Surface((r*2+20,r*2+20),pygame.SRCALPHA)
        pygame.draw.circle(gs,(255,80,80,28),(r+10,r+10),r+8)
        screen.blit(gs,(sx-r-10,sy-r-10))

    # Gravity portals
    for g in GRAV:
        gx=int(g["x"]-cam_x)
        if gx>WIDTH+TILE*2 or gx<-TILE*2: continue
        gy=int(g["y"]); gw=g["w"]; gh=g["h"]
        pulse=int(50+40*abs(math.sin(frame*0.08)))
        gs=pygame.Surface((gw+40,gh+20),pygame.SRCALPHA)
        pygame.draw.rect(gs,(180,80,255,pulse),(20,10,gw,gh))
        screen.blit(gs,(gx-20,gy-10))
        pygame.draw.rect(screen,C_GRAV,(gx,gy,gw,gh),2)
        # chevron arrows showing flip direction
        mid=gy+gh//2
        for off in [-16,0,16]:
            ay=mid+off
            pygame.draw.line(screen,C_GRAV,(gx-10,ay),(gx+gw//2,ay-8),2)
            pygame.draw.line(screen,C_GRAV,(gx+gw//2,ay-8),(gx+gw+10,ay),2)

    # End gate
    tx=int(EG["x"]+ox)
    pygame.draw.rect(screen,C_WIN,(tx,int(EG["y"]),EG["w"],EG["h"]))
    g=pygame.Surface((34,EG["h"]+24),pygame.SRCALPHA)
    g.fill((0,255,136,30)); screen.blit(g,(tx-12,int(EG["y"])-12))

def draw_player():
    if not player: return
    px=int(player["x"]-cam_x); py=int(player["y"])
    col=C_GRAV if grav_flipped else C_MAIN
    surf=pygame.Surface((PW+24,PH+24),pygame.SRCALPHA)
    gl=pygame.Surface((PW+24,PH+24),pygame.SRCALPHA)
    gl.fill((*col,28)); surf.blit(gl,(0,0))
    pygame.draw.rect(surf,(*col,185),(12,12,PW,PH))
    pygame.draw.rect(surf,col,(12,12,PW,PH),2)
    cx,cy=12+PW//2,12+PH//2
    pygame.draw.rect(surf,(255,255,255,215),(cx-8,cy-8,16,16))
    pygame.draw.rect(surf,(*col,135),(cx-4,cy-4,8,8))
    if not player["on_ground"] and not player["dead"]:
        surf=pygame.transform.rotate(surf,-math.degrees(air_rot))
    screen.blit(surf,(px+PW//2-surf.get_width()//2,
                      py+PH//2-surf.get_height()//2))

def draw_hud():
    pct=max(0.0,min(1.0,cam_x/max(1,total_w-WIDTH)))
    bar=C_GRAV if grav_flipped else C_MAIN
    pygame.draw.rect(screen,(35,35,60),(0,0,WIDTH,5))
    pygame.draw.rect(screen,bar,(0,0,int(WIDTH*pct),5))
    screen.blit(FONT.render("STEREO MADNESS",True,(255,255,255)),(14,10))
    ps=FONT.render(f"{int(pct*100)}%",True,(255,255,255))
    screen.blit(ps,(WIDTH//2-ps.get_width()//2,10))
    ss=FONT.render(f"SCORE: {score}",True,(255,255,255))
    screen.blit(ss,(WIDTH-ss.get_width()-14,10))
    screen.blit(FONT.render(f"ATTEMPT {attempt}",True,(85,85,125)),(14,HEIGHT-20))
    hs=FONT.render("SPACE / CLICK to jump",True,(50,50,80))
    screen.blit(hs,(WIDTH-hs.get_width()-14,HEIGHT-20))
    if grav_flipped:
        fl=FONT_LG.render("GRAVITY FLIPPED",True,C_GRAV)
        bg=pygame.Surface((fl.get_width()+20,fl.get_height()+8),pygame.SRCALPHA)
        bg.fill((20,0,40,160))
        screen.blit(bg,(WIDTH//2-fl.get_width()//2-10,HEIGHT//2-58))
        screen.blit(fl,(WIDTH//2-fl.get_width()//2,HEIGHT//2-54))
    best=saves.get("best")
    if best:
        bs=FONT.render(f"Best: {best}",True,(50,50,80))
        screen.blit(bs,(WIDTH//2-bs.get_width()//2,HEIGHT-20))

def draw_menu():
    draw_bg()
    t1=FONT_XL.render("GEOMETRY",True,C_MAIN)
    t2=FONT_XL.render("DASH",True,(255,0,255))
    sub=FONT.render("STEREO MADNESS",True,(110,110,150))
    go=FONT_LG.render("PRESS SPACE OR CLICK TO PLAY",True,(190,190,255))
    it=FONT.render(
        "spikes  ·  platforms  ·  blocks  ·  sawblades  ·  gravity portals",
        True,(60,60,95))
    bt=saves.get("best")
    bs=FONT.render(f"Best score: {bt}" if bt else "Not yet played",True,(65,65,95))
    screen.blit(t1,(WIDTH//2-t1.get_width()//2,95))
    screen.blit(t2,(WIDTH//2-t2.get_width()//2,150))
    screen.blit(sub,(WIDTH//2-sub.get_width()//2,220))
    screen.blit(go,(WIDTH//2-go.get_width()//2,278))
    screen.blit(it,(WIDTH//2-it.get_width()//2,326))
    screen.blit(bs,(WIDTH//2-bs.get_width()//2,370))

def draw_death():
    ov=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
    ov.fill((180,0,0,28)); screen.blit(ov,(0,0))
    t1=FONT_LG.render("CRASHED!",True,C_DEATH)
    t2=FONT.render(message,True,(200,200,200))
    screen.blit(t1,(WIDTH//2-t1.get_width()//2,HEIGHT//2-28))
    screen.blit(t2,(WIDTH//2-t2.get_width()//2,HEIGHT//2+18))

def draw_win():
    ov=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
    ov.fill((0,28,0,160)); screen.blit(ov,(0,0))
    t1=FONT_XL.render("LEVEL COMPLETE!",True,C_WIN)
    t2=FONT.render(f"Score: {score}    Attempts: {attempt}",True,(165,255,190))
    t3=FONT.render("SPACE or CLICK to play again",True,(70,150,90))
    screen.blit(t1,(WIDTH//2-t1.get_width()//2,HEIGHT//2-58))
    screen.blit(t2,(WIDTH//2-t2.get_width()//2,HEIGHT//2+10))
    screen.blit(t3,(WIDTH//2-t3.get_width()//2,HEIGHT//2+48))

# ── main loop ─────────────────────────────────────────────────────────────
# ── DEBUG SCROLL MODE (remove before publishing) ─────────────────────────
# Hold TAB to freeze the game and scroll freely through the level.
# LEFT/RIGHT arrows scroll slowly, hold SHIFT for fast scroll.
# TAB releases and resumes normal play from where you left off.
DEBUG_SCROLL = False   # True while Tab is held

running=True
while running:
    clock.tick(FPS)

    keys = pygame.key.get_pressed()

    for event in pygame.event.get():
        if event.type==pygame.QUIT: running=False
        if event.type==pygame.KEYDOWN:
            if event.key==pygame.K_TAB:
                DEBUG_SCROLL=True
                # start a level if not already playing so there are tiles to view
                if state not in("playing","dead","win"): start_game()
            if event.key in(pygame.K_SPACE,pygame.K_UP): do_jump()
        if event.type==pygame.KEYUP:
            if event.key==pygame.K_TAB: DEBUG_SCROLL=False
            if event.key in(pygame.K_SPACE,pygame.K_UP): jump_held=False
        if event.type==pygame.MOUSEBUTTONDOWN: do_jump()
        if event.type==pygame.MOUSEBUTTONUP: jump_held=False

    if DEBUG_SCROLL and state in("playing","dead","win"):
        # freeze physics, scroll with arrow keys
        scroll_speed = 20 if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] else 5
        if keys[pygame.K_RIGHT]: cam_x = min(cam_x+scroll_speed, max(0,total_w-WIDTH))
        if keys[pygame.K_LEFT]:  cam_x = max(cam_x-scroll_speed, 0)
        # draw everything frozen
        draw_bg(); draw_tiles(); draw_player()
        for p in particles: p.draw(screen,cam_x)
        draw_hud()
        # overlay debug info
        pct = int(max(0,min(100,cam_x/max(1,total_w-WIDTH)*100)))
        dbg1 = FONT.render(f"[DEBUG SCROLL]  cam_x={int(cam_x)}  {pct}%", True, (255,255,0))
        dbg2 = FONT.render("ARROWS=scroll  SHIFT=fast  release TAB to resume", True, (200,200,0))
        bg=pygame.Surface((dbg1.get_width()+16, 42), pygame.SRCALPHA)
        bg.fill((0,0,0,160))
        screen.blit(bg,(WIDTH//2-dbg1.get_width()//2-8, HEIGHT//2-21))
        screen.blit(dbg1,(WIDTH//2-dbg1.get_width()//2, HEIGHT//2-18))
        screen.blit(dbg2,(WIDTH//2-dbg2.get_width()//2, HEIGHT//2+4))
    elif state=="menu":
        frame+=1; draw_menu()
        for p in particles: p.update()
        particles[:]=[p for p in particles if p.life>0]
        for p in particles: p.draw(screen,0)
    else:
        update(); draw_bg(); draw_tiles(); draw_player()
        for p in particles: p.draw(screen,cam_x)
        draw_hud()
        if state=="dead": draw_death()
        elif state=="win": draw_win()

    pygame.display.flip()

pygame.quit()
sys.exit()