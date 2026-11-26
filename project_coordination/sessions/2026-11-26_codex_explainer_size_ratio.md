# Method C explainer size-ratio clarification

Re-rendered only scene 05 and scene 06 and reassembled the video. The other eleven scene PNGs match commit 452bd64af3e13e1944afd384b0ec871d39f26882 byte for byte. No simulation input, state, summary, report, UEL or PBS job was modified or executed.

The Case 3 adaptive corridor generator specifies h_bg=2.0 mm and h_ref=0.140 mm. Ratio 14.2857143; squared area ratio 204.0816327, shown as approximately 14 and 200. All nodal interpolation values remain unchanged; decimal checks verify 0.825 / 0.775 / 0.725 / 0.675 round half-up to 0.83 / 0.78 / 0.73 / 0.68.

Video is H.264 1920x1080 at 10 fps, 870 frames, duration 87.000 s. All 13 midpoint frames compared with their PNGs in sequence and the affected scenes were visually inspected. Initial render had a colorbar-label overlap; corrected before final encoding. Video SHA-256 4D8D7A966602A9FA154213267B882F42FE382301FDCE3EF7885B6927BF55D3D8. Full playback initiated.
