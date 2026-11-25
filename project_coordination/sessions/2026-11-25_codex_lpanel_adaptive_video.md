# L-panel adaptive mesh and damage video

Assembled existing coarse and cycle 1–10 side-by-side mesh/damage PNGs from `models/mode_II_or_l_panel/295_method_c_lpanel/local_windows_adaptive_run/` into `results/animations/lpanel_adaptive_mesh_damage_cycles_0_10.mp4`. This is a sequence of discrete saved end states, not intermediate solver frames. Cycle 11 is excluded because it did not complete. No simulation, transfer, or HPC submission was performed.

Video: H.264, 2160 x 1080, 24 fps, 30.04 s; SHA-256 CD6449F59BFF161F8B4E37B996CE5A148C367E031C4E80599DE7100EDCDD1189. Source images retain their own cycle, load, mesh and damage labels. ffprobe metadata and full ffmpeg decode passed. Base commit 7b6e8911e064ce91db1de8ad44428b1c64685c9a. Master goal remains OPEN.