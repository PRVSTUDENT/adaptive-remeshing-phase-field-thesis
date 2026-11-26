# Method C explainer interpolation fix

Added a conceptual nodal-interpolation scene and revised the remeshing and transfer captions. Scene 5 also had to be re-rendered to implement its requested caption. Images for former Scenes 1?4 and 7?12 remain byte-for-byte unchanged and are stored with shifted file names; in-video counters are overlaid to reflect the 13-scene sequence.

Midpoint and centre values were checked against the supplied corners; element means 0.825 / 0.775 / 0.725 / 0.675 were rounded half-up to 0.83 / 0.78 / 0.73 / 0.68. Initial floating-point equality assertion failed; repaired using a numerical tolerance and separate exact decimal checks. No simulation, PBS, UEL, existing report or summary changed.

H.264 1920x1080 10 fps, 870 frames, 87.000 seconds; all 13 midpoint frames checked in order against source PNGs and ten unaffected images checked byte-for-byte against commit ec16cbf84e5daa33245f8501f9c9bab812274567. The transfer reveal and captions were visually reviewed. Video SHA-256 964a13c12cdf84a3a7e624217e11cb3b54e8e829e2142b5b2328749ce5b19ec7. Full playback was initiated.
