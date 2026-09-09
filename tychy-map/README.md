# Tychy — ECOFACTOR map

Square (1000×1000) vector map of Tychy (Poland) in the ECOFACTOR design
system: dark background, brand-green city contour and location markers,
no labels — only the city outline, the main streets and the Paprocański lake.

## Files
- `map_tychy_ecofactor.svg` — source vector, scalable, square.
- `map_tychy_ecofactor.png` — 2000×2000 raster export.
- `preview.html` — standalone viewer.
- `generate.py` — generator that produces the SVG.

## Markers
10 green markers placed at the addresses shown as red pins on the source
reference: Rynek 6, Biblioteczna 24, Barona 30, Edukacji 7, al. Bielska 82,
al. Niepodległości 49, Szpital Megrez, Marszałka Piłsudskiego 20,
gen. Sikorskiego 20, gen. Sikorskiego 100.

## Notes
Geometry (city boundary, lake, streets, marker positions) is traced from the
two supplied Google-Maps references — live OSM/geocoding data was not
reachable from the build environment. It is a stylised brand map, faithful to
the references' shape and relative positions, not a survey-accurate map. To
regenerate: `python3 generate.py`.

## Colors (ECOFACTOR tokens)
- Brand green `#3AF185` — contour + markers
- Background `#191919`–`#242424` (eerie black)
- Streets `#3d3d3d` / `#565656`
