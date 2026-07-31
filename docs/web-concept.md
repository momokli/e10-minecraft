# Web Concept — Enigmatica 10

> **Target:** Desktop-first, responsive down to mobile (≥375px)
> **Tech:** Flask, Jinja2 templates, plain CSS (Tailwind optional)
> **Domains:** `e10.projectmellon.de` (all pages), `grafana.e10.projectmellon.de` (separate)
> **Design tool:** Google Stitch — this doc serves as the prompt/spec

---

## Site Map

```
e10.projectmellon.de/
├── /                     Public Info Page
├── /admin                Admin Dashboard (auth-gated)
├── /map                  Live Map (Bluemap embed)
├── /donate               Donation Page (Ko-fi)
└── /api/*                REST API (existing, JSON only)
```

| Page            | Auth    | Purpose                                    |
|-----------------|---------|--------------------------------------------|
| `/`             | None    | Server status, online players, MOTD, links |
| `/admin`        | Token   | Whitelist, backups, RCON, "Go!" button     |
| `/map`          | None    | Full-page Bluemap iframe                   |
| `/donate`       | None    | Ko-fi embed + supporter wall               |

---

## Global Design System

### Mood
Dark, immersive, "Minecraft-Nether-Portal"-vibe meets modern tech dashboard.
Deep purples and teal/cyan accents. Subtle pixel-art touches without being retro.

### Color Palette
| Role          | Hex       | Usage                            |
|---------------|-----------|----------------------------------|
| Background    | `#0f0b1a` | Main page background             |
| Surface       | `#1a1530` | Cards, nav, footer               |
| Surface Alt   | `#241f3d` | Hover states, secondary cards    |
| Primary       | `#6c5ce7` | Buttons, active tabs, links      |
| Accent        | `#00e5ff` | Highlights, status indicators    |
| Success       | `#00e676` | Online badge, success toasts     |
| Warning       | `#ffab40` | Warning badges, PROD indicator   |
| Danger        | `#ff5252` | Stop buttons, offline badge      |
| Text Primary  | `#e8e6f0` | Headings, body text              |
| Text Muted    | `#8884a5` | Secondary text, placeholders     |
| Border        | `#2a2545` | Card borders, dividers           |

### Typography
- **Headings:** `Inter` or `Space Grotesk` — bold, geometric, modern
- **Body:** `Inter` — clean, readable
- **Monospace:** `JetBrains Mono` — player names, commands, logs
- **Scale:** 12/14/16/20/24/32/48px

### Spacing & Grid
- Base unit: `4px` → spacings: 8, 12, 16, 20, 24, 32, 48, 64
- Max content width: `1200px` centered
- Cards: `border-radius: 12px`, subtle `box-shadow` with primary color glow on hover

### Icon Style
- Phosphor Icons or Lucide — clean, consistent, modern
- Size: 20px inline, 24px standalone, 32px feature icons

### Motion
- Page transitions: subtle fade (200ms ease)
- Hover: scale(1.02) on cards, background shift on buttons
- Loading: skeleton screens with shimmer animation
- Toast notifications: slide in from top-right, auto-dismiss 3s

---

## Page 1: Public Info Page `/`

### Purpose
First thing players see. Quick answer to "Is the server up? Who's online?"

### Layout — Desktop

```
┌─────────────────────────────────────────────────────────┐
│  NAV BAR (sticky top)                                    │
│  [⚡ E10 Logo]   Info · Map · Donate    [🟢 5 online]   │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────────────┐  ┌──────────────────────┐ │
│  │   HERO                    │  │   MOTD CARD           │ │
│  │                           │  │                        │ │
│  │   🟢 SERVER ONLINE        │  │   "Welcome to E10!    │ │
│  │   IP: e10.projectmellon.  │  │   Season 1 just        │ │
│  │        de                 │  │   started..."          │ │
│  │                           │  │                        │ │
│  │   VERSION 1.21.1          │  └──────────────────────┘ │
│  │   MODPACK Enigmatica 10                                │
│  └──────────────────────────┘                              │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │   PLAYERS ONLINE (5)                              │   │
│  │                                                    │   │
│  │   [🧑 PlayerHead] Yizzl                            │   │
│  │   [🧑 PlayerHead] Momo                             │   │
│  │   [🧑 PlayerHead] Steve                            │   │
│  │   [🧑 PlayerHead] Alex           … and 1 more      │   │
│  │                                                    │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │ 🗺 LIVE MAP │  │ 💬 DISCORD │  │ 💰 SUPPORT │        │
│  │  → /map     │  │  → invite  │  │  → /donate  │        │
│  └────────────┘  └────────────┘  └────────────┘        │
│                                                          │
├─────────────────────────────────────────────────────────┤
│  FOOTER: © Enigmatica 10 · Modpack v1.30 · MC 1.21.1    │
└─────────────────────────────────────────────────────────┘
```

### Layout — Mobile (<768px)
- Stack everything vertically
- Hero becomes compact: status dot + IP + player count in one row
- MOTD card below hero
- Player list becomes horizontal avatar row (max 5 shown, "+N" overflow)
- Quick-link cards become icon-only horizontal row

### Components
| Component        | Data Source            | Refresh |
|------------------|------------------------|---------|
| Server Status    | `/api/prod/players`    | 10s     |
| Player Count     | `/api/prod/players`    | 10s     |
| Player List      | `/api/prod/players`    | 10s     |
| MOTD             | `/api/prod/motd`       | 30s     |
| Quick Links      | static                 | -       |
| Server Info      | static config          | -       |

### Edge Cases
- **Server offline:** Hero shows 🔴 OFFLINE badge, player list hidden, MOTD shows last known
- **No players:** "No one is online right now. Be the first!" with CTA
- **API error:** Show "Could not reach server" with retry button

---

## Page 2: Admin Dashboard `/admin`

### Purpose
Full server control for admins. All destructive actions behind confirmation dialogs.

### Auth
Simple token-based. Token set via env var `ADMIN_TOKEN`.
Access: `?token=xxx` query param or cookie after first auth.
Unauthorized → redirect to `/admin/login` with simple form.

### Layout — Desktop

```
┌─────────────────────────────────────────────────────────┐
│  NAV BAR                                                │
│  [⚡ E10 Admin]  PROD · TEST          [👤 Admin] [← Back]│
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────────────┐  ┌────────────────────────────┐│
│  │ ⚙️ SERVER CONTROL    │  │ 👥 PLAYERS (3)             ││
│  │                      │  │                             ││
│  │ [▶ Start] [⏹ Stop]  │  │  Yizzl          [⚡ Kick]  ││
│  │ [🔄 Restart]         │  │  Momo           [⚡ Kick]  ││
│  │                      │  │  Steve          [⚡ Kick]  ││
│  │ 💾 [Save All]        │  │                             ││
│  │                      │  │  [🚀 GO! Release All]      ││
│  │ 📟 RCON Console       │  │                             ││
│  │ ┌──────────────────┐ │  └────────────────────────────┘│
│  │ │ > say Hello      │ │                                │
│  │ │ [Sent] Hello     │ │   ┌──────────────────────────┐ │
│  │ │ > _              │ │   │ 📋 WHITELIST              │ │
│  │ └──────────────────┘ │   │                            │ │
│  └─────────────────────┘   │  [+ Add Player___] [Add]   │ │
│                             │                            │ │
│  ┌─────────────────────┐   │  Yizzl                [✕]  │ │
│  │ 💾 BACKUPS           │   │  Momo                 [✕]  │ │
│  │                      │   │  Steve                [✕]  │ │
│  │ [🔄 Create Backup]   │   │                            │ │
│  │                      │   └──────────────────────────┘ │
│  │ Snapshots:           │                                │
│  │ 20260731-1200 [↩]   │   ┌──────────────────────────┐ │
│  │ 20260731-0800 [↩]   │   │ 📢 MOTD                  │ │
│  │ 20260730-2000 [↩]   │   │                            │ │
│  │                      │   │ Line 1: [Welcome to E10!] │ │
│  └─────────────────────┘   │ Line 2: [Season 1 started] │ │
│                             │ [Set MOTD]                 │ │
│                             └──────────────────────────┘ │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Layout — Mobile
- Single column, cards stack vertically
- Tab bar PROD/TEST at top (same as current)
- RCON console collapses to a "Open Console" button → fullscreen overlay
- Player list compresses, kick becomes swipe-to-reveal
- Backup snapshots become scrollable horizontal list

### Components
| Component         | Data Source                    | Actions                             |
|-------------------|--------------------------------|-------------------------------------|
| Instance Tabs     | local state                    | Switch PROD/TEST context            |
| Server Control    | -                              | Start, Stop, Restart, Save All      |
| Player List       | `/api/{inst}/players`          | Kick player, **GO! (release cage)** |
| RCON Console      | `/api/{inst}/cmd`              | Send arbitrary RCON command         |
| Whitelist         | `/api/{inst}/whitelist`        | Add, Remove player                  |
| MOTD              | `/api/{inst}/motd`             | Set line1, line2                    |
| Backups           | `/api/{inst}/backup`, `/backups`| Create, List, Restore              |

### "Go!" Button (Waiting Cage Release)
This is the key Yizzl feature:
1. All players in Adventure mode, trapped in 20×20 WorldBorder
2. Admin presses **GO!** → one action triggers:
   - `gamemode survival @a`
   - `worldborder set 59999968`
   - `say ▶ The cage is open! Good luck!`

The button should be prominent, pulsing, maybe with a dramatic animation.

### Edge Cases
- **Double-confirm** for Stop, Restart, Restore, GO!
- **Restore flow:** Confirm → Stop → Extract → "Server must be manually started"
- **Kick:** Confirm dialog with player name
- **RCON timeout:** Show "Command timed out" after 5s
- **Backup failure:** Show error with retry

---

## Page 3: Live Map `/map`

### Purpose
Full-viewport Bluemap embed. Minimal chrome — just a back link and fullscreen toggle.

### Layout

```
┌─────────────────────────────────────────────────────────┐
│  [← Back to E10]                    [⛶ Fullscreen]      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│                                                          │
│                   BLUEMAP IFRAME                          │
│                   (100vw × calc(100vh - 48px))           │
│                                                          │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Components
| Component    | Detail                                    |
|--------------|-------------------------------------------|
| Back link    | Returns to `/`                            |
| Fullscreen   | Toggle `requestFullscreen()` on iframe    |
| Iframe       | Proxied or direct Bluemap URL             |

### Edge Cases
- **Bluemap not running:** Show "Map is currently unavailable" placeholder
- **Mobile:** Back link + fullscreen overlay bar auto-hides after 3s

---

## Page 4: Donation Page `/donate`

### Purpose
Support the server. Ko-fi integration + optional supporter recognition.

### Layout

```
┌─────────────────────────────────────────────────────────┐
│  NAV BAR: [← Info] [🗺 Map] [💬 Discord]                 │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │                                                    │   │
│  │           💜 Support Enigmatica 10                 │   │
│  │                                                    │   │
│  │   Servers cost money. If you enjoy playing,        │   │
│  │   consider buying us a coffee! ☕                   │   │
│  │                                                    │   │
│  │         [KO-FI BUTTON / WIDGET]                    │   │
│  │                                                    │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │   🌟 SUPPORTER WALL (optional, future)             │   │
│  │                                                    │   │
│  │   "Thanks to Momo, Yizzl, Steve..."                │   │
│  │                                                    │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Components
| Component       | Detail                                     |
|-----------------|--------------------------------------------|
| Ko-fi Widget    | Embedded Ko-fi button + donation panel     |
| Supporter Wall  | Manual list or Ko-fi API (future)          |
| Navigation      | Same nav as info page                      |

---

## Navigation & Shared Elements

### Nav Bar (all pages except /map)
- **Left:** ⚡ E10 Logo + page title
- **Center (desktop):** Info · Map · Donate · Discord
- **Right:** Player count badge (🟢 N online) on public pages, instance selector on admin
- **Mobile:** Hamburger menu, player count always visible

### Footer (all pages)
- `© Enigmatica 10 · Modpack v1.30 · MC 1.21.1 · NeoForge`
- Subtle, muted color, small text

### Toast Notifications
- Slide in from top-right
- Types: success (green), error (red), info (blue), warning (orange)
- Auto-dismiss 3s, dismissable via ×
- Stack multiple toasts

---

## User Flows

### Flow 1: Player checks server status
```
Player visits / → Sees "🟢 ONLINE · 3 players" → Sees MOTD → Clicks Map → Plays
```

### Flow 2: Player wants on whitelist
```
Player visits / → Clicks Discord → Asks in #whitelist-requests
Admin visits /admin → Whitelist card → Types name → Clicks Add → Toast "Added!"
```

### Flow 3: Admin releases waiting cage
```
Event starts → Admin visits /admin → Sees 5 players in cage
→ Presses [🚀 GO!] → Confirm dialog → Players released → Toast "Cage opened!"
```

### Flow 4: Admin creates backup
```
Admin visits /admin → Backups card → [Create Backup] → Spinner → Toast "Done"
→ Snapshots list updates
```

### Flow 5: Admin restores world
```
Admin visits /admin → Backups → [↩ Restore] on snapshot
→ Confirm (⚠ This will stop the server) → Server stops → Backup extracts
→ Toast "Restored. Start server manually." → Admin presses [▶ Start]
```

---

## API Endpoints (existing + new)

| Method | Path                              | Description                        | Status   |
|--------|-----------------------------------|------------------------------------|----------|
| GET    | `/api/{inst}/players`             | Player list                        | exists   |
| GET    | `/api/{inst}/whitelist`           | Whitelist list                     | exists   |
| POST   | `/api/{inst}/whitelist/add`       | Add to whitelist                   | exists   |
| POST   | `/api/{inst}/whitelist/remove`    | Remove from whitelist              | exists   |
| GET    | `/api/{inst}/motd`                | Get MOTD                           | exists   |
| POST   | `/api/{inst}/motd`                | Set MOTD                           | exists   |
| POST   | `/api/{inst}/cmd`                 | Send RCON command                  | exists   |
| POST   | `/api/{inst}/backup`              | Create backup                      | exists   |
| GET    | `/api/{inst}/backups`             | List snapshots                     | exists   |
| POST   | `/api/{inst}/restore`             | Restore snapshot                   | exists   |
| GET    | `/api/status`                     | Aggregate server status            | **new**  |
| POST   | `/api/{inst}/go`                  | Release waiting cage               | **new**  |
| POST   | `/api/{inst}/kick`                | Kick player                        | **new**  |
| GET    | `/api/{inst}/tps`                 | TPS via spark/metrics (if avail)   | **new**  |

---

## Technical Notes for Implementation

### Template Structure (Jinja2)
```
webui/
├── app.py
├── templates/
│   ├── base.html          # Nav, footer, toast container, CSS vars
│   ├── index.html         # Public info page
│   ├── admin.html         # Admin dashboard
│   ├── admin_login.html   # Simple token login form
│   ├── map.html           # Bluemap embed
│   └── donate.html        # Ko-fi page
├── static/
│   ├── style.css
│   └── script.js
├── requirements.txt
└── Dockerfile
```

### CSS Approach
Plain CSS with CSS custom properties (as defined in design system above).
No framework dependency keeps it lightweight — the Flask container is small.

### JS Approach
Vanilla JS with `fetch()` for API calls. No framework needed at this scale.
If complexity grows, consider **htmx** + **Alpine.js** for interactivity.

### Auth Strategy
- `ADMIN_TOKEN` env var on Flask container
- Check `?token=` query param or `admin_token` cookie
- Login form at `/admin/login` sets cookie
- All `/api/*` endpoints already open — add token check for destructive ones

---

## Open Questions

1. **Auth:** Simple shared token, or do we want per-admin tokens later?
2. **Discord widget:** Embed Discord server widget on `/` or just a link?
3. **Bluemap URL:** Proxied through Flask or direct to Bluemap container port?
4. **TPS display:** Worth showing on public page or admin-only?
5. **Logo:** Do we have a server logo/icon to use? (e.g. 64×64 for nav, 256×256 for hero)
