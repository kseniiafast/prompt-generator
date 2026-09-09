#!/usr/bin/env python3
"""Generate an ECOFACTOR-styled square vector map of Tychy.
Geometry traced from the two user reference images (boundary + street/markers).
No external network/data needed. Outputs a 1000x1000 SVG."""

# ----------------------------------------------------------------------------
# 1. Reference-image pixel coordinates (digitised by eye from the two refs)
# ----------------------------------------------------------------------------
# Reference 1 (boundary map) ~601 x 333 px. Boundary outline, clockwise from N.
IMG1_BOUNDARY = [
    (283, 82), (315, 85), (348, 91), (382, 92), (410, 100), (431, 112),
    (440, 138), (446, 165), (449, 184), (438, 205), (417, 221), (398, 235),
    (372, 252), (344, 266), (321, 281), (306, 298), (296, 300), (283, 285),
    (268, 271), (250, 262), (231, 244), (216, 224), (205, 202), (199, 178),
    (198, 160), (203, 138), (214, 116), (233, 99), (256, 88), (283, 82),
]
# Lake (Jezioro Paprocanskie) defined in image2 px so it aligns with the
# southern marker (Sikorskiego 100), which sits just off its northern shore.
IMG2_LAKE = [
    (360, 905), (405, 866), (458, 856), (502, 872), (523, 905),
    (512, 946), (470, 972), (412, 968), (372, 938),
]

# Landmark correspondences: image2 px  ->  image1 px  (shared places)
# image2 (street map) ~1109 x 1039 px
LANDMARKS = [
    # name,            img2 (x,y),      img1 (x,y)
    ("SRODMIESCIE",   (365, 462),      (258, 183)),
    ("ZWAKOW",        (340, 620),      (262, 214)),
    ("PAPROCANY",     (605, 775),      (300, 250)),
    ("URBANOWICE",    (900, 590),      (352, 206)),
    ("STARE_TYCHY",   (355, 285),      (250, 150)),
    ("TYCHY_CENTER",  (735, 418),      (322, 172)),
]

# The 10 markers, in image2 px (positions of the red pins on ref 2)
MARKERS_IMG2 = [
    ("Rynek 6",                         (432, 328)),
    ("Biblioteczna 24",                 (455, 375)),
    ("Barona 30",                       (408, 402)),
    ("Edukacji 7",                      (500, 419)),
    ("al. Bielska 82",                  (437, 471)),
    ("al. Niepodleglosci 49",           (565, 525)),
    ("Szpital Megrez",                  (655, 535)),
    ("Marsz. Pilsudskiego 20",          (475, 640)),
    ("Gen. Sikorskiego 20",             (405, 671)),
    ("Gen. Sikorskiego 100",            (550, 847)),
]

# Main streets, digitised in image2 px as polylines (major arteries only).
STREETS_IMG2 = {
    # DK44 (Mikolowska / al. Jana Pawla II / Oswiecimska) NW->center->SE
    "DK44": [(40, 30), (150, 120), (250, 200), (360, 300), (470, 360),
             (600, 400), (720, 420), (820, 470), (900, 560), (980, 640)],
    # DK1 (Beskidzka / Katowicka) N->S on the east-centre
    "DK1": [(790, 200), (785, 300), (770, 390), (720, 470), (640, 560),
            (610, 660), (605, 760), (600, 860), (600, 950)],
    # S1 expressway, far east edge
    "S1": [(860, 250), (900, 360), (930, 470), (955, 600), (980, 740)],
    # al. Bielska  (center -> SW)
    "al_Bielska": [(430, 470), (330, 560), (230, 650), (140, 720), (60, 780)],
    # al. Niepodleglosci / Beskidzka central vertical
    "al_Niepodleglosci": [(560, 300), (562, 400), (565, 520), (520, 620), (470, 720)],
    # Edukacji (central, past hospital)
    "Edukacji": [(500, 300), (520, 380), (545, 470), (600, 540), (655, 600)],
    # Sikorskiego (down toward Paprocany)
    "Sikorskiego": [(405, 620), (450, 700), (500, 780), (550, 847), (600, 900)],
    # Piłsudskiego cross street
    "Pilsudskiego": [(300, 600), (400, 630), (475, 640), (560, 640), (640, 650)],
}

# ----------------------------------------------------------------------------
# 2. Solve affine transform  image2 -> image1  (least squares, pure python)
# ----------------------------------------------------------------------------
def solve_affine(src, dst):
    """Return (a,b,c,d,e,f) mapping (x,y)->(a x+b y+c, d x+e y+f) via normal eqs."""
    # Build for x' = a x + b y + c   and   y' = d x + e y + f  separately.
    def lstsq3(pts_src, target):
        # Solve 3x3 normal equations for [p,q,r] minimising sum (p*x+q*y+r - t)^2
        Sxx=Sxy=Sx=Syy=Sy=Sn=0.0
        Stx=Sty=St=0.0
        for (x, y), t in zip(pts_src, target):
            Sxx+=x*x; Sxy+=x*y; Sx+=x; Syy+=y*y; Sy+=y; Sn+=1
            Stx+=t*x; Sty+=t*y; St+=t
        # Matrix A = [[Sxx,Sxy,Sx],[Sxy,Syy,Sy],[Sx,Sy,Sn]], rhs=[Stx,Sty,St]
        A=[[Sxx,Sxy,Sx],[Sxy,Syy,Sy],[Sx,Sy,Sn]]
        rhs=[Stx,Sty,St]
        return gauss3(A, rhs)
    srcpts=[s for s in src]
    tx=[d[0] for d in dst]
    ty=[d[1] for d in dst]
    a,b,c = lstsq3(srcpts, tx)
    d,e,f = lstsq3(srcpts, ty)
    return (a,b,c,d,e,f)

def gauss3(A, rhs):
    import copy
    M=[row[:]+[rhs[i]] for i,row in enumerate(A)]
    n=3
    for i in range(n):
        # pivot
        p=max(range(i,n), key=lambda r: abs(M[r][i]))
        M[i],M[p]=M[p],M[i]
        piv=M[i][i]
        for j in range(i,n+1): M[i][j]/=piv
        for r in range(n):
            if r!=i:
                fac=M[r][i]
                for j in range(i,n+1): M[r][j]-=fac*M[i][j]
    return [M[0][3],M[1][3],M[2][3]]

src=[l[1] for l in LANDMARKS]
dst=[l[2] for l in LANDMARKS]
AFF=solve_affine(src,dst)
def img2_to_img1(x,y):
    a,b,c,d,e,f=AFF
    return (a*x+b*y+c, d*x+e*y+f)

# report fit residuals
res=[]
for name,s,dd in LANDMARKS:
    px,py=img2_to_img1(*s)
    res.append(((px-dd[0])**2+(py-dd[1])**2)**0.5)
print("affine residuals (img1 px):", [round(r,1) for r in res])

# ----------------------------------------------------------------------------
# 3. Projection image1 px -> square 1000x1000 viewBox (fit boundary bbox)
# ----------------------------------------------------------------------------
xs=[p[0] for p in IMG1_BOUNDARY]; ys=[p[1] for p in IMG1_BOUNDARY]
minx,maxx=min(xs),max(xs); miny,maxy=min(ys),max(ys)
bw=maxx-minx; bh=maxy-miny
VB=1000.0
MARGIN=140.0          # padding around the city inside the square
span=VB-2*MARGIN
scale=span/max(bw,bh)
# center the (possibly non-square) bbox in the square
offx=MARGIN+(span-bw*scale)/2
offy=MARGIN+(span-bh*scale)/2
def img1_to_vb(x,y):
    return (offx+(x-minx)*scale, offy+(y-miny)*scale)
def img2_to_vb(x,y):
    return img1_to_vb(*img2_to_img1(x,y))

# ----------------------------------------------------------------------------
# 4. Path helpers
# ----------------------------------------------------------------------------
def catmull_rom(points, closed=False, k=1.0):
    """Return an SVG path string through points using Catmull-Rom -> bezier."""
    p=points[:]
    if len(p)<3:
        d="M "+" L ".join(f"{x:.2f},{y:.2f}" for x,y in p)
        return d+(" Z" if closed else "")
    if closed:
        pts=[p[-1]]+p+[p[0],p[1]]
    else:
        pts=[p[0]]+p+[p[-1]]
    d=f"M {p[0][0]:.2f},{p[0][1]:.2f} "
    n=len(pts)
    for i in range(1,n-2):
        p0,p1,p2,p3=pts[i-1],pts[i],pts[i+1],pts[i+2]
        c1x=p1[0]+(p2[0]-p0[0])/6.0*k
        c1y=p1[1]+(p2[1]-p0[1])/6.0*k
        c2x=p2[0]-(p3[0]-p1[0])/6.0*k
        c2y=p2[1]-(p3[1]-p1[1])/6.0*k
        d+=f"C {c1x:.2f},{c1y:.2f} {c2x:.2f},{c2y:.2f} {p2[0]:.2f},{p2[1]:.2f} "
    if closed: d+="Z"
    return d

boundary_vb=[img1_to_vb(*p) for p in IMG1_BOUNDARY]
# rotate the point list so the closed spline does not start/close at the
# northern apex (avoids a visible cusp there); start on the smooth east side.
_rot=12
boundary_vb=boundary_vb[_rot:]+boundary_vb[:_rot]
lake_vb=[img2_to_vb(*p) for p in IMG2_LAKE]
boundary_path=catmull_rom(boundary_vb, closed=True, k=0.9)
lake_path=catmull_rom(lake_vb, closed=True, k=1.0)

streets_vb={name:[img2_to_vb(*pt) for pt in pts] for name,pts in STREETS_IMG2.items()}
markers_vb=[(name, img2_to_vb(*pt)) for name,pt in MARKERS_IMG2]

# ----------------------------------------------------------------------------
# 5. Clip streets to the city boundary (point-in-polygon) so lines stay inside
# ----------------------------------------------------------------------------
def point_in_poly(x,y,poly):
    inside=False; n=len(poly); j=n-1
    for i in range(n):
        xi,yi=poly[i]; xj,yj=poly[j]
        if ((yi>y)!=(yj>y)) and (x < (xj-xi)*(y-yi)/(yj-yi+1e-9)+xi):
            inside=not inside
        j=i
    return inside

# use a densified boundary polygon for the in/out test
poly_test=boundary_vb

def clip_polyline(pts):
    """Split a polyline into segments that fall inside the boundary."""
    segs=[]; cur=[]
    for (x,y) in pts:
        if point_in_poly(x,y,poly_test):
            cur.append((x,y))
        else:
            if len(cur)>=2: segs.append(cur)
            cur=[]
    if len(cur)>=2: segs.append(cur)
    return segs

# ----------------------------------------------------------------------------
# 6. Emit SVG
# ----------------------------------------------------------------------------
GREEN="#3AF185"; GREEN2="#3DD078"; GREEN3="#23A859"
BG_D="#191919"; BG_L="#242424"
STREET_MIN="#3d3d3d"; STREET_MAJ="#565656"
LAKE_FILL="#1d2a27"; LAKE_STROKE="#26433a"

def street_path(name):
    d=""
    for seg in clip_polyline(streets_vb[name]):
        d+=catmull_rom(seg, closed=False, k=1.0)+" "
    return d.strip()

MAJOR={"DK44","DK1","S1"}
street_svg=[]
for name in streets_vb:
    d=street_path(name)
    if not d: continue
    if name in MAJOR:
        w=2.8; col=STREET_MAJ
    else:
        w=1.8; col=STREET_MIN
    street_svg.append(f'    <path d="{d}" fill="none" stroke="{col}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>')
street_svg="\n".join(street_svg)

# marker pin: teardrop, tip at (0,0), body above. Scaled group placed per marker.
def pin(x,y,idx):
    s=1.0
    return f'''    <g transform="translate({x:.2f},{y:.2f})" class="pin">
      <ellipse cx="0" cy="4" rx="9" ry="3.2" fill="#000" opacity="0.28"/>
      <path d="M0,2 C-8,-9 -12,-16 -12,-23 A12,12 0 1 1 12,-23 C12,-16 8,-9 0,2 Z"
            fill="url(#pinGrad)" stroke="#0d3f24" stroke-width="1"/>
      <circle cx="0" cy="-23" r="4.6" fill="#0f2b1c"/>
    </g>'''

pins_svg="\n".join(pin(x,y,i) for i,(_,(x,y)) in enumerate(markers_vb))

svg=f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000" width="1000" height="1000" role="img" aria-label="Map of Tychy">
  <defs>
    <radialGradient id="bg" cx="50%" cy="44%" r="72%">
      <stop offset="0%" stop-color="{BG_L}"/>
      <stop offset="100%" stop-color="{BG_D}"/>
    </radialGradient>
    <linearGradient id="pinGrad" x1="0" y1="-35" x2="0" y2="2" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="{GREEN}"/>
      <stop offset="100%" stop-color="{GREEN3}"/>
    </linearGradient>
    <filter id="glow" x="-40%" y="-40%" width="180%" height="180%">
      <feGaussianBlur stdDeviation="4" result="b"/>
      <feComponentTransfer in="b" result="bd"><feFuncA type="linear" slope="0.75"/></feComponentTransfer>
      <feMerge><feMergeNode in="bd"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="pinGlow" x="-60%" y="-60%" width="220%" height="220%">
      <feDropShadow dx="0" dy="1.5" stdDeviation="3.5" flood-color="{GREEN}" flood-opacity="0.45"/>
    </filter>
    <clipPath id="cityClip"><path d="{boundary_path}"/></clipPath>
  </defs>

  <rect x="0" y="0" width="1000" height="1000" fill="url(#bg)"/>

  <!-- faint city fill -->
  <path d="{boundary_path}" fill="{GREEN}" fill-opacity="0.045" stroke="none"/>

  <!-- streets, clipped to city -->
  <g clip-path="url(#cityClip)" opacity="0.95">
{street_svg}
  </g>

  <!-- lake (clipped to the city) -->
  <g clip-path="url(#cityClip)">
    <path d="{lake_path}" fill="{LAKE_FILL}" stroke="{LAKE_STROKE}" stroke-width="1.5"/>
  </g>

  <!-- city boundary (hero) -->
  <g filter="url(#glow)">
    <path d="{boundary_path}" fill="none" stroke="{GREEN}" stroke-width="3.0"
          stroke-linejoin="round" opacity="0.96"/>
  </g>

  <!-- markers -->
  <g filter="url(#pinGlow)">
{pins_svg}
  </g>
</svg>'''

with open("map_tychy_ecofactor.svg","w") as f:
    f.write(svg)
print("wrote map_tychy_ecofactor.svg", len(svg), "bytes")
