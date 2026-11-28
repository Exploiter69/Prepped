# UI reference v2 — implementation notes

## Source review

The latest user-supplied design export contains nine artboards: Today (Main.dc.html), Rehearsal stage (Practice.dc.html), Career Studios (Career.dc.html), Memory (Memory.dc.html), Design system (DesignSystem.dc.html), Onboarding (Onboarding.dc.html), Voice interaction states (Voice.dc.html), Learning lesson player (Lesson.dc.html), and Practice feedback (Feedback.dc.html).

The export is a usable core-screen reference, but it is not yet a complete application design package. It does not include dedicated artboards for Progress, Profile, Settings, Help, Search, notification preferences, or the full empty/error/loading/offline states for every destination. Today references Progress and Profile in navigation without supplying their full visual boards.

The HTML artboards are design exports, not production app screens. Their buttons and links must not be treated as proof of working product behavior.

## Implementation

The UI implementation is being applied to the existing HTML/CSS/JavaScript app rather than replacing its architecture or adding a frontend framework.

- Added static/ui-reference.css as a layered visual treatment.
- Loaded it after the existing stylesheet in static/index.html.
- Applied the design's cream canvas, warm surface, deep teal primary, restrained borders, serif display typography, and desktop sidebar / mobile bottom navigation treatment.
- Kept existing app logic and accessibility behavior in place.
- No hosted font dependency was added. The design export references Google Fonts; this implementation uses a local system serif fallback to preserve the project's no-external-runtime-request goal.

## Remaining implementation work

This is the first visual alignment pass, not a claim of 100% pixel parity. The next passes need to align each existing view and state against its matching artboard, verify responsive layouts and interaction states, and add the missing design boards before the entire app can be signed off as complete.
