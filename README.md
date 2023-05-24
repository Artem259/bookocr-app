# BookOcr-Console

### Console application based on BookOcr tool.

#### Running the application.
The application is launching in the Windows command line:
1. Navigate to the ``main`` folder.
2. Run ``main.exe --help`` to get a complete description of the launch configuration.

Run command examples:\
``main.exe "../image.png" "../out" --s``\
``main.exe "../image.png" "../out" --s --m``\
``main.exe "../images/" "../out" --config "../config.json" --sconfig "../stats_config.json" --s --m``

#### Config and stats config files structure.

- Default config file:
```
{
    "blur_kernel": 0,
    "invert_colors": false,
    "otsu_threshold1": 0,
    "otsu_threshold2": 255,

    "fix_rotation": true,
    "hough_max_threshold": 500,
    "hough_min_lines": 10,
    "hough_max_lines": 30,
    "hough_angle_range": 0.5,
    "hough_angle_step": 1,

    "cell_size_multiplier": 2,
    "canny_edges_threshold1": 85.0,
    "canny_edges_threshold2": 255,
    "text_assumption_threshold1": 0.2,
    "text_assumption_threshold2": 0.6,
    "text_assumption_min_occurrences": 2,
    "text_areas_deviation": 1,
    "text_area_padding": 0.5,

    "text_denoising_threshold": 0.08,

    "lines_hist_window": 0.25,
    "lines_hist_frequency": 1.6,

    "space_threshold": 0.15,
    "paragraph_spaces": 4
}
```

- Default stats config file:
```
{
    "first_color": [0, 0, 255],
    "second_color": [0, 255, 0],
    "histograms_color": [100, 100, 100],
    "overlay_opacity": 0.25,
    "padding": 0,
    "lines_thickness": 2,
    "text_denoise_indicators_width": 20
}
```


