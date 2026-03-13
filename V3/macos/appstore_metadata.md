# App Store Connect — GameMotion Submission Checklist

Copy-paste these into App Store Connect when setting up the listing.

---

## App Information

**App Name (30 chars max)**
GameMotion

**Subtitle (30 chars max)**
Control Games With Your Body

**Bundle ID**
org.gamemotion.app

**Category (Primary)**
Games → Utilities
*(or: Utilities → Games)*

**Age Rating**
4+ (no objectionable content)

---

## App Store Listing (English – United States)

**Description (4000 chars max)**

```
GameMotion turns your webcam into a game controller — no hardware required.

Using your device's camera, GameMotion tracks your body posture in real time and converts your movements into keyboard inputs for any game. Lean left to strafe, raise your arm to jump, crouch to dodge — you design the controls.

HOW IT WORKS
• Your camera detects 33 body landmarks using on-device machine learning (no video is ever sent to the cloud)
• You train GameMotion to recognise your chosen poses by recording a few example samples
• GameMotion matches your live pose to trained actions and sends the corresponding keystrokes to your game

FULLY CUSTOMISABLE
• Create per-game action profiles — each game gets its own set of poses and key mappings
• Train as many actions as you need: movement, attacks, abilities, menus
• Adjust detection sensitivity and cooldown timing in Settings

PRIVACY FIRST
• All pose detection runs entirely on your Mac — no camera data leaves your device
• No account required, no subscription, no data collection

ACCESSIBILITY
• Designed for players who want or need hands-free control
• Works with any game that accepts keyboard input

REQUIREMENTS
• Mac with a built-in or external webcam
• macOS 13 Ventura or later
• Accessibility permission (to send keystrokes to games — granted once in System Settings)
```

**Keywords (100 chars max — comma separated)**
```
gesture control,motion gaming,body tracking,hands-free,pose detection,accessibility,game controller
```

**What's New (for updates)**
```
Initial release.
```

---

## Pricing & Availability

**Price:** Free
*(or set a price — discuss with client)*

**Availability:** All countries/regions (recommended)

---

## App Privacy

Complete the privacy nutrition label in App Store Connect.
GameMotion's data practices:

| Data Type | Collected | Linked to User | Used for Tracking |
|---|---|---|---|
| Camera / Video | No (processed on-device only) | — | No |
| Usage Data | No | — | No |
| Crash Data | No | — | No |

Select **"No data collected"** unless you add analytics later.

**Privacy Policy URL** *(required — must be live before submission)*
You need to host a privacy policy page. Minimum content:
- What data is collected (none, in this case)
- That camera is used on-device only
- Contact email

A free option: create a page at notion.so or a simple GitHub Pages site.

---

## Review Information

**Sign-In Required:** No

**Notes for App Review Team:**
```
GameMotion is a body-motion game controller. It uses:

1. Camera — to detect the user's body pose using MediaPipe, entirely on-device.
   No video or image data is transmitted externally.

2. Accessibility — to send keyboard events to games. The user is prompted to
   grant this in System Settings → Privacy & Security → Accessibility on first
   launch. Without this, the app can still train poses but cannot send keystrokes.

The app bundles a Python runtime (PyInstaller) as a helper tool to handle
pose detection and the local API server. This helper inherits the app's
sandbox entitlements.

To test: launch the app, grant Accessibility when prompted, open any game,
and move in front of the camera. The dashboard at http://127.0.0.1:8000
shows live confidence scores and lets you train new poses.
```

---

## Screenshots Required

Mac App Store requires screenshots at these sizes:

| Display | Resolution |
|---|---|
| MacBook Pro 16" (primary) | 2560 × 1600 |
| MacBook Pro 14" | 2560 × 1664 |

**Minimum:** 1 screenshot per size, up to 10.
**Recommended shots:**
1. Dashboard / main view with live camera preview
2. Training screen (recording a new pose)
3. Profiles / key mapping screen
4. Settings screen
5. Accessibility permission prompt (shows the onboarding flow)

*Take screenshots by running the app locally (Xcode → Run) and using
Cmd+Shift+3 or the macOS Screenshot tool.*

---

## Submission Steps (when Apple Developer account is ready)

1. Log into [appstoreconnect.apple.com](https://appstoreconnect.apple.com)
2. Create a new macOS app with bundle ID `org.gamemotion.app`
3. Fill in the listing above
4. In Xcode: open `V3/macos/GameMotion.xcodeproj`
5. Set **Team** in Signing & Capabilities to your team
6. Change signing in `project.yml`:
   ```
   CODE_SIGN_STYLE: Manual
   CODE_SIGN_IDENTITY: Apple Distribution
   ```
7. Run `V3/macos/build_mas.sh` to produce the archive
8. In Xcode Organizer → Distribute → App Store Connect → Upload
9. Wait ~30 min for processing, then submit for review
