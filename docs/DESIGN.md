# Hangar Design System: "Blueprint"

## Visual Philosophy
Hangar follows a drafting-table concept for machine-room control:
- Quiet, disciplined line work (1px borders, no drop shadows).
- Monochrome surfaces with color reserved exclusively for status lamps and badges.
- Faint 24px blueprint background grid (~4% opacity).
- No flashy gradients, no cream/terracotta styles, no generic rounded cards.

## Color Tokens & Themes

### Dark: "Cyanotype"
- `--bg`: `#0A2036`
- `--surface`: `#0F2D49`
- `--surface-2`: `#153A5C`
- `--line`: `#27537A`
- `--text`: `#E8F1F8`
- `--muted`: `#8DAFC8`
- `--primary`: `#E8F1F8` (text: `#0A2036`)

### Light: "Tracing Paper"
- `--bg`: `#E8EDF0`
- `--surface`: `#F6F8F9`
- `--surface-2`: `#DCE4E9`
- `--line`: `#B7C5CF`
- `--text`: `#0C2237`
- `--muted`: `#51677A`
- `--primary`: `#0C2237` (text: `#F6F8F9`)

### Status Colors
- `--run`: `#34D8A5` (dark) / `#0B8E68` (light)
- `--start`: `#63B8FF` (dark) / `#1A6DB5` (light)
- `--warn`: `#F4B94E` (dark) / `#9A6107` (light)
- `--err`: `#FF6B7C` (dark) / `#C22E42` (light)
- `--off`: `#6F8DA6` (dark) / `#75899A` (light)

## Typography
- **Primary**: Bricolage Grotesque (variable, condensed/heavy for page titles, normal for UI controls).
- **Monospace**: JetBrains Mono for logs, shell commands, paths, and port displays.
- Sentence case throughout; no all-caps labels or tracked-out caps.

## Interactive Controls
- `<PowerSwitch>`: Smooth 180 ms toggle with status lamp, `role="switch"`, `aria-checked`.
- Lamp: Glowing soft shadow in dark mode, flat ring in light mode. Status is accompanied by lamp + icon + label text (never color alone).
