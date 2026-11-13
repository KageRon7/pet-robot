#pragma once
// BU DOSYA animasyon_aktar.py TARAFINDAN OTOMATIK OLUSTURULMUSTUR.
#include "animasyon_tanimlari.h"

const char CURIOUS_JSON[] = R"json({
  "format": "C3-taslak",
  "name": "meraklı",
  "emotion": "curious",
  "loop": false,
  "duration_ms": 2400,
  "keys": [
    {
      "t_ms": 0,
      "ease": "linear",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.9,
        "eye_size": 1.1,
        "pupil": 0.9,
        "sparkle": 1,
        "look_x": -0.35,
        "look_y": 0,
        "brow_show": true,
        "brow_left": -6,
        "brow_right": 8,
        "brow_height": 0.4,
        "mouth": "w",
        "mouth_open": 0.5,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": -10,
        "head_pan": -25,
        "head_tilt": 5,
        "ear_left": 1,
        "ear_right": 1,
        "ms": 0
      }
    },
    {
      "t_ms": 500,
      "ease": "snap",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.9,
        "eye_size": 1.25,
        "pupil": 1.2,
        "sparkle": 1,
        "look_x": 0.5,
        "look_y": 0,
        "brow_show": true,
        "brow_left": 8,
        "brow_right": 8,
        "brow_height": 0.6,
        "mouth": "o",
        "mouth_open": 0.2,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 8,
        "head_pan": 20,
        "head_tilt": 15,
        "ear_left": 1,
        "ear_right": 1,
        "ms": 500
      }
    },
    {
      "t_ms": 1000,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.9,
        "eye_size": 1.25,
        "pupil": 1.25,
        "sparkle": 1,
        "look_x": 0.5,
        "look_y": 0,
        "brow_show": true,
        "brow_left": -6,
        "brow_right": 8,
        "brow_height": 0.3,
        "mouth": "w",
        "mouth_open": 0.3,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": -10,
        "head_pan": 10,
        "head_tilt": 28,
        "ear_left": 0.6,
        "ear_right": 0.6,
        "ms": 500
      }
    },
    {
      "t_ms": 1400,
      "ease": "bounce",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.9,
        "eye_size": 1.15,
        "pupil": 1.25,
        "sparkle": 1,
        "look_x": 0.5,
        "look_y": 0,
        "brow_show": true,
        "brow_left": -6,
        "brow_right": 8,
        "brow_height": 0.8,
        "mouth": "w",
        "mouth_open": 1,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 15,
        "head_pan": -10,
        "head_tilt": -5,
        "ear_left": 1,
        "ear_right": 1,
        "ms": 400
      }
    },
    {
      "t_ms": 2000,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.9,
        "eye_size": 1.1,
        "pupil": 0.9,
        "sparkle": 1,
        "look_x": -0.35,
        "look_y": 0,
        "brow_show": true,
        "brow_left": -6,
        "brow_right": 8,
        "brow_height": 0.4,
        "mouth": "w",
        "mouth_open": 0.85,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": -10,
        "head_pan": -25,
        "head_tilt": 10,
        "ear_left": 1,
        "ear_right": 0.55,
        "ms": 600
      }
    },
    {
      "t_ms": 2400,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.9,
        "eye_size": 1.1,
        "pupil": 0.9,
        "sparkle": 1,
        "look_x": -0.35,
        "look_y": 0,
        "brow_show": true,
        "brow_left": -6,
        "brow_right": 8,
        "brow_height": 0.4,
        "mouth": "w",
        "mouth_open": 0.5,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": -10,
        "head_pan": -25,
        "head_tilt": 5,
        "ear_left": 1,
        "ear_right": 1,
        "ms": 400
      }
    }
  ]
})json";

const char CURIOUS2_JSON[] = R"json({
  "format": "C3-taslak",
  "name": "meraklı ",
  "emotion": "curious",
  "loop": false,
  "duration_ms": 3030,
  "keys": [
    {
      "t_ms": 240,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.9,
        "eye_size": 1.1,
        "pupil": 0.9,
        "sparkle": 1,
        "look_x": -1,
        "look_y": 0,
        "brow_show": true,
        "brow_left": -6,
        "brow_right": 8,
        "brow_height": 0.4,
        "mouth": "smile",
        "mouth_open": 0.42,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": -10,
        "head_pan": -25,
        "head_tilt": 10,
        "ear_left": 1,
        "ear_right": 0.55,
        "ms": 240
      }
    },
    {
      "t_ms": 950,
      "ease": "bounce",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.9,
        "eye_size": 1.1,
        "pupil": 0.9,
        "sparkle": 1,
        "look_x": 1,
        "look_y": 0,
        "brow_show": true,
        "brow_left": -4,
        "brow_right": 6,
        "brow_height": 0.4,
        "mouth": "smile",
        "mouth_open": 0.42,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "colors": {
          "line": "#2b2a33",
          "iris": "#6b4a3a",
          "blush": "#f09aa6",
          "tear": "#5dade2",
          "face_bg": "#fbf8f3",
          "head": "#8e929c"
        }
      },
      "pose": {
        "body_yaw": -10,
        "head_pan": -25,
        "head_tilt": 10,
        "ear_left": 0.55,
        "ear_right": 1,
        "ms": 710
      }
    },
    {
      "t_ms": 1490,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.9,
        "eye_size": 1.1,
        "pupil": 0.9,
        "sparkle": 1,
        "look_x": -0.55,
        "look_y": 0,
        "brow_show": true,
        "brow_left": 8,
        "brow_right": -6,
        "brow_height": 0.4,
        "mouth": "smile",
        "mouth_open": 0.42,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": -10,
        "head_pan": -25,
        "head_tilt": 10,
        "ear_left": 1,
        "ear_right": 0.66,
        "ms": 540
      }
    },
    {
      "t_ms": 1960,
      "ease": "stop",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.9,
        "eye_size": 1.1,
        "pupil": 0.92,
        "sparkle": 1,
        "look_x": 0.52,
        "look_y": 0,
        "brow_show": true,
        "brow_left": 9,
        "brow_right": -4,
        "brow_height": 0.4,
        "mouth": "smile",
        "mouth_open": 0.62,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "colors": {
          "line": "#2b2a33",
          "iris": "#6b4a3a",
          "blush": "#f09aa6",
          "tear": "#5dade2",
          "face_bg": "#fbf8f3",
          "head": "#8e929c"
        }
      },
      "pose": {
        "body_yaw": -10,
        "head_pan": -25,
        "head_tilt": 10,
        "ear_left": 0.66,
        "ear_right": 1,
        "ms": 470
      }
    },
    {
      "t_ms": 2480,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.9,
        "eye_size": 1.1,
        "pupil": 0.96,
        "sparkle": 1,
        "look_x": 0.1,
        "look_y": 0,
        "brow_show": true,
        "brow_left": 9,
        "brow_right": 2,
        "brow_height": 0.4,
        "mouth": "smile",
        "mouth_open": 1,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "colors": {
          "line": "#2b2a33",
          "iris": "#6b4a3a",
          "blush": "#f09aa6",
          "tear": "#5dade2",
          "face_bg": "#fbf8f3",
          "head": "#8e929c"
        }
      },
      "pose": {
        "body_yaw": -10,
        "head_pan": -25,
        "head_tilt": 10,
        "ear_left": 0.61,
        "ear_right": 0.61,
        "ms": 520
      }
    },
    {
      "t_ms": 3030,
      "ease": "smooth",
      "face": {
        "eye_shape": "arc",
        "eye_open": 0.9,
        "eye_size": 1.1,
        "pupil": 0.9,
        "sparkle": 1,
        "look_x": 0,
        "look_y": 0,
        "brow_show": true,
        "brow_left": 10,
        "brow_right": 10,
        "brow_height": 0.4,
        "mouth": "w",
        "mouth_open": 1,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": -10,
        "head_pan": -25,
        "head_tilt": 10,
        "ear_left": 0.55,
        "ear_right": 0.55,
        "ms": 550
      }
    }
  ]
})json";

const char HAPPY_JSON[] = R"json({
  "format": "C3-taslak",
  "name": "Im so Zıp Zıp ",
  "emotion": "happy",
  "loop": true,
  "duration_ms": 8900,
  "keys": [
    {
      "t_ms": 0,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.9,
        "eye_size": 1,
        "pupil": 0.9,
        "sparkle": 0.8,
        "look_x": 0,
        "look_y": 0,
        "brow_show": true,
        "brow_left": 0,
        "brow_right": 0,
        "brow_height": 0,
        "mouth": "y",
        "mouth_open": 0.25,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": false,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 0,
        "head_tilt": 0,
        "ear_left": 1,
        "ear_right": 1,
        "ms": 0
      }
    },
    {
      "t_ms": 1100,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.9,
        "eye_size": 1.15,
        "pupil": 1.1,
        "sparkle": 1,
        "look_x": 0,
        "look_y": 0,
        "brow_show": true,
        "brow_left": 0,
        "brow_right": 0,
        "brow_height": 0,
        "mouth": "smile",
        "mouth_open": 0.5,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": false,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 0,
        "head_tilt": 0,
        "ear_left": 1,
        "ear_right": 1,
        "ms": 1100
      }
    },
    {
      "t_ms": 2200,
      "ease": "smooth",
      "face": {
        "eye_shape": "arc",
        "eye_open": 0.9,
        "eye_size": 1,
        "pupil": 0.9,
        "sparkle": 0.8,
        "look_x": 0,
        "look_y": 0,
        "brow_show": false,
        "brow_left": 0,
        "brow_right": 0,
        "brow_height": 0,
        "mouth": "w",
        "mouth_open": 0.6,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 6,
        "head_pan": 10,
        "head_tilt": 8,
        "ear_left": 1,
        "ear_right": 1,
        "ms": 1100
      }
    },
    {
      "t_ms": 3200,
      "ease": "smooth",
      "face": {
        "eye_shape": "arc",
        "eye_open": 0.9,
        "eye_size": 1,
        "pupil": 0.9,
        "sparkle": 1,
        "look_x": 0,
        "look_y": 0,
        "brow_show": false,
        "brow_left": 0,
        "brow_right": 0,
        "brow_height": 0,
        "mouth": "fang",
        "mouth_open": 0.5,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2b2a33",
          "iris": "#6b4a3a",
          "blush": "#f09aa6",
          "tear": "#5dade2",
          "face_bg": "#fbf8f3",
          "head": "#8e929c"
        }
      },
      "pose": {
        "body_yaw": -3,
        "head_pan": -6,
        "head_tilt": 4,
        "ear_left": 0.9,
        "ear_right": 0.9,
        "ms": 1000
      }
    },
    {
      "t_ms": 4200,
      "ease": "bounce",
      "face": {
        "eye_shape": "arc",
        "eye_open": 0.9,
        "eye_size": 1,
        "pupil": 0.9,
        "sparkle": 1,
        "look_x": 0,
        "look_y": 0,
        "brow_show": false,
        "brow_left": 0,
        "brow_right": 0,
        "brow_height": 0,
        "mouth": "grin",
        "mouth_open": 0.9,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": -6,
        "head_pan": -10,
        "head_tilt": 14,
        "ear_left": 1,
        "ear_right": 1,
        "ms": 1000
      }
    },
    {
      "t_ms": 5200,
      "ease": "smooth",
      "face": {
        "eye_shape": "arc",
        "eye_open": 0.9,
        "eye_size": 1,
        "pupil": 0.9,
        "sparkle": 0.8,
        "look_x": 0,
        "look_y": 0,
        "brow_show": false,
        "brow_left": 0,
        "brow_right": 0,
        "brow_height": 0,
        "mouth": "tongue",
        "mouth_open": 0.6,
        "mouth_width": 1,
        "mouth_x": 0.15,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2b2a33",
          "iris": "#6b4a3a",
          "blush": "#f09aa6",
          "tear": "#5dade2",
          "face_bg": "#fbf8f3",
          "head": "#8e929c"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 8,
        "head_tilt": 8,
        "ear_left": 1,
        "ear_right": 1,
        "ms": 1000
      }
    },
    {
      "t_ms": 6200,
      "ease": "smooth",
      "face": {
        "eye_shape": "narrow",
        "eye_open": 0.7,
        "eye_size": 1.05,
        "pupil": 0.85,
        "sparkle": 0.6,
        "look_x": -0.4,
        "look_y": 0,
        "brow_show": true,
        "brow_left": 8,
        "brow_right": -10,
        "brow_height": 0.2,
        "mouth": "smirk",
        "mouth_open": 0.5,
        "mouth_width": 1,
        "mouth_x": 0.25,
        "mouth_tilt": -6,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 5,
        "head_tilt": 6,
        "ear_left": 1,
        "ear_right": 0.7,
        "ms": 1000
      }
    },
    {
      "t_ms": 7100,
      "ease": "smooth",
      "face": {
        "eye_shape": "arc",
        "eye_open": 0.9,
        "eye_size": 1,
        "pupil": 0.9,
        "sparkle": 0.8,
        "look_x": 0,
        "look_y": 0,
        "brow_show": false,
        "brow_left": 0,
        "brow_right": 0,
        "brow_height": 0,
        "mouth": "smirk",
        "mouth_open": 0.7,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 8,
        "head_pan": 12,
        "head_tilt": 8,
        "ear_left": 1,
        "ear_right": 0.7,
        "ms": 900
      }
    },
    {
      "t_ms": 8000,
      "ease": "smooth",
      "face": {
        "eye_shape": "arc",
        "eye_open": 0.9,
        "eye_size": 1,
        "pupil": 0.9,
        "sparkle": 1,
        "look_x": 0,
        "look_y": 0,
        "brow_show": false,
        "brow_left": 0,
        "brow_right": 0,
        "brow_height": 0,
        "mouth": "pout",
        "mouth_open": 0.6,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2b2a33",
          "iris": "#6b4a3a",
          "blush": "#f09aa6",
          "tear": "#5dade2",
          "face_bg": "#fbf8f3",
          "head": "#8e929c"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 0,
        "head_tilt": 6,
        "ear_left": 1,
        "ear_right": 1,
        "ms": 900
      }
    },
    {
      "t_ms": 8900,
      "ease": "smooth",
      "face": {
        "eye_shape": "arc",
        "eye_open": 0.9,
        "eye_size": 1,
        "pupil": 0.9,
        "sparkle": 1,
        "look_x": 0,
        "look_y": 0,
        "brow_show": false,
        "brow_left": 0,
        "brow_right": 0,
        "brow_height": 0,
        "mouth": "smile",
        "mouth_open": 0.7,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 0,
        "head_tilt": 4,
        "ear_left": 0.9,
        "ear_right": 0.9,
        "ms": 900
      }
    }
  ]
})json";

const char HEAD_EXPLOSION_BUUM_JSON[] = R"json({
  "format": "C3-taslak",
  "name": "Baş Patlaması(BuUM)",
  "emotion": "idle",
  "loop": false,
  "duration_ms": 11800,
  "keys": [
    {
      "t_ms": 0,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 1,
        "eye_size": 1.15,
        "pupil": 0.95,
        "sparkle": 1,
        "look_x": 0.45,
        "look_y": -0.15,
        "brow_show": true,
        "brow_left": -4,
        "brow_right": 12,
        "brow_height": 0.5,
        "mouth": "o",
        "mouth_open": 0.15,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": false,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 22,
        "head_tilt": 14,
        "ear_left": 1,
        "ear_right": 0.75,
        "ms": 0
      }
    },
    {
      "t_ms": 1200,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 1,
        "eye_size": 1.3,
        "pupil": 0.75,
        "sparkle": 1,
        "look_x": 0,
        "look_y": 0,
        "brow_show": true,
        "brow_left": -4,
        "brow_right": -4,
        "brow_height": 0.9,
        "mouth": "o",
        "mouth_open": 0.7,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 0,
        "head_tilt": 0,
        "ear_left": 1,
        "ear_right": 1,
        "ms": 1200
      }
    },
    {
      "t_ms": 2600,
      "ease": "stop",
      "face": {
        "eye_shape": "round",
        "eye_open": 1,
        "eye_size": 1.4,
        "pupil": 0.5,
        "sparkle": 0.3,
        "look_x": 0,
        "look_y": 0,
        "brow_show": true,
        "brow_left": -6,
        "brow_right": -6,
        "brow_height": 1,
        "mouth": "o",
        "mouth_open": 0.7,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": false,
        "sweat": true,
        "gloom": 0.25,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2b2a33",
          "iris": "#6b4a3a",
          "blush": "#f09aa6",
          "tear": "#5dade2",
          "face_bg": "#fbf8f3",
          "head": "#8e929c"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 6,
        "head_tilt": 10,
        "ear_left": 0.9,
        "ear_right": 0.9,
        "ms": 1400
      }
    },
    {
      "t_ms": 3600,
      "ease": "stop",
      "face": {
        "eye_shape": "spiral",
        "eye_open": 0.9,
        "eye_size": 1,
        "pupil": 0.9,
        "sparkle": 0.8,
        "look_x": 0,
        "look_y": 0,
        "brow_show": true,
        "brow_left": 10,
        "brow_right": 10,
        "brow_height": 0.8,
        "mouth": "wobble",
        "mouth_open": 0.45,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": false,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 12,
        "head_tilt": 8,
        "ear_left": 0.3,
        "ear_right": 0.9,
        "ms": 1000
      }
    },
    {
      "t_ms": 4700,
      "ease": "stop",
      "face": {
        "eye_shape": "spiral",
        "eye_open": 0.9,
        "eye_size": 1,
        "pupil": 0.9,
        "sparkle": 0.8,
        "look_x": 0,
        "look_y": 0,
        "brow_show": true,
        "brow_left": 10,
        "brow_right": 10,
        "brow_height": 0.8,
        "mouth": "wobble",
        "mouth_open": 0.45,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": false,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2b2a33",
          "iris": "#6b4a3a",
          "blush": "#f09aa6",
          "tear": "#5dade2",
          "face_bg": "#fbf8f3",
          "head": "#8e929c"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": -12,
        "head_tilt": 8,
        "ear_left": 0.3,
        "ear_right": 0.9,
        "ms": 1100
      }
    },
    {
      "t_ms": 6000,
      "ease": "bounce",
      "face": {
        "eye_shape": "narrow",
        "eye_open": 0.8,
        "eye_size": 1,
        "pupil": 0.9,
        "sparkle": 0.5,
        "look_x": 0,
        "look_y": 0,
        "brow_show": true,
        "brow_left": -16,
        "brow_right": -16,
        "brow_height": -0.3,
        "mouth": "grimace",
        "mouth_open": 0,
        "mouth_width": 0.65,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": false,
        "sweat": true,
        "gloom": 0,
        "rage": 0.4,
        "anger_mark": true,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 0,
        "head_tilt": 0,
        "ear_left": 0.5,
        "ear_right": 0.5,
        "ms": 1300
      }
    },
    {
      "t_ms": 7400,
      "ease": "stop",
      "face": {
        "eye_shape": "narrow",
        "eye_open": 0.85,
        "eye_size": 1.05,
        "pupil": 0.9,
        "sparkle": 0.5,
        "look_x": 0,
        "look_y": 0,
        "brow_show": true,
        "brow_left": -26,
        "brow_right": -26,
        "brow_height": -0.5,
        "mouth": "shout",
        "mouth_open": 0.75,
        "mouth_width": 1,
        "mouth_x": 0.1,
        "mouth_tilt": -12,
        "tears": 0,
        "blush": false,
        "sweat": true,
        "gloom": 0,
        "rage": 0.9,
        "anger_mark": true,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 0,
        "head_tilt": -5,
        "ear_left": 0.3,
        "ear_right": 0.3,
        "ms": 1400
      }
    },
    {
      "t_ms": 8800,
      "ease": "snap",
      "face": {
        "eye_shape": "blank",
        "eye_open": 0.5,
        "eye_size": 1.15,
        "pupil": 0.9,
        "sparkle": 0.8,
        "look_x": 0,
        "look_y": 0,
        "brow_show": false,
        "brow_left": 24,
        "brow_right": 24,
        "brow_height": 0.9,
        "mouth": "zigzag",
        "mouth_open": 0.2,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": false,
        "sweat": true,
        "gloom": 0.6,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 0,
        "head_tilt": -10,
        "ear_left": 0.05,
        "ear_right": 0.05,
        "ms": 1400
      }
    },
    {
      "t_ms": 10200,
      "ease": "snap",
      "face": {
        "eye_shape": "blank",
        "eye_open": 0.9,
        "eye_size": 1.15,
        "pupil": 0.9,
        "sparkle": 0.8,
        "look_x": 0,
        "look_y": 0,
        "brow_show": true,
        "brow_left": 24,
        "brow_right": 24,
        "brow_height": 0.9,
        "mouth": "shout",
        "mouth_open": 0.85,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": false,
        "sweat": true,
        "gloom": 1,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 0,
        "head_tilt": 0,
        "ear_left": 0.1,
        "ear_right": 0.1,
        "ms": 1400
      }
    },
    {
      "t_ms": 11800,
      "ease": "stop",
      "face": {
        "eye_shape": "closed",
        "eye_open": 0.5,
        "eye_size": 1.15,
        "pupil": 0.9,
        "sparkle": 0.8,
        "look_x": 0,
        "look_y": 0,
        "brow_show": false,
        "brow_left": 24,
        "brow_right": 24,
        "brow_height": 0.9,
        "mouth": "smile",
        "mouth_open": 0.45,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": false,
        "sweat": false,
        "gloom": 0.8,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 0,
        "head_tilt": -10,
        "ear_left": 0,
        "ear_right": 0,
        "ms": 1600
      }
    }
  ]
})json";

const char IDLE_JSON[] = R"json({
  "format": "C3-taslak",
  "name": "Bekleme Ekranı ",
  "emotion": "idle",
  "loop": true,
  "duration_ms": 15800,
  "keys": [
    {
      "t_ms": 0,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.9,
        "eye_size": 1,
        "pupil": 0.9,
        "sparkle": 0.8,
        "look_x": 0,
        "look_y": 0,
        "brow_show": true,
        "brow_left": 0,
        "brow_right": 0,
        "brow_height": 0,
        "mouth": "y",
        "mouth_open": 0.25,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": false,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 0,
        "head_tilt": 0,
        "ear_left": 1,
        "ear_right": 1,
        "ms": 0
      }
    },
    {
      "t_ms": 1600,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.9,
        "eye_size": 1,
        "pupil": 0.9,
        "sparkle": 0.8,
        "look_x": -0.5,
        "look_y": 0,
        "brow_show": true,
        "brow_left": 0,
        "brow_right": 0,
        "brow_height": 0,
        "mouth": "y",
        "mouth_open": 0.25,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": false,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": -4,
        "head_pan": -15,
        "head_tilt": 0,
        "ear_left": 0.8,
        "ear_right": 1,
        "ms": 1600
      }
    },
    {
      "t_ms": 3200,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.9,
        "eye_size": 1,
        "pupil": 1.1,
        "sparkle": 0.8,
        "look_x": -0.3,
        "look_y": -0.15,
        "brow_show": true,
        "brow_left": -2,
        "brow_right": 8,
        "brow_height": 0,
        "mouth": "o",
        "mouth_open": 0.12,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": false,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": -4,
        "head_pan": -8,
        "head_tilt": 10,
        "ear_left": 0.8,
        "ear_right": 0.8,
        "ms": 1600
      }
    },
    {
      "t_ms": 4800,
      "ease": "linear",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.15,
        "eye_size": 1,
        "pupil": 1.1,
        "sparkle": 0.8,
        "look_x": -0.3,
        "look_y": -0.15,
        "brow_show": true,
        "brow_left": -2,
        "brow_right": 8,
        "brow_height": 0,
        "mouth": "o",
        "mouth_open": 0.12,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": false,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": -4,
        "head_pan": -8,
        "head_tilt": 10,
        "ear_left": 0.8,
        "ear_right": 0.8,
        "ms": 1600
      }
    },
    {
      "t_ms": 5000,
      "ease": "linear",
      "face": {
        "eye_shape": "round",
        "eye_open": 1,
        "eye_size": 1,
        "pupil": 1.1,
        "sparkle": 0.8,
        "look_x": -0.3,
        "look_y": -0.15,
        "brow_show": true,
        "brow_left": -2,
        "brow_right": 8,
        "brow_height": 0,
        "mouth": "o",
        "mouth_open": 0.12,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": false,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": -4,
        "head_pan": -8,
        "head_tilt": 10,
        "ear_left": 0.8,
        "ear_right": 0.8,
        "ms": 200
      }
    },
    {
      "t_ms": 6400,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 1,
        "eye_size": 1.05,
        "pupil": 1.1,
        "sparkle": 1,
        "look_x": 0.2,
        "look_y": -0.15,
        "brow_show": true,
        "brow_left": -2,
        "brow_right": 8,
        "brow_height": 0,
        "mouth": "smile",
        "mouth_open": 0.4,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": -4,
        "head_pan": 5,
        "head_tilt": 5,
        "ear_left": 0.8,
        "ear_right": 0.8,
        "ms": 1400
      }
    },
    {
      "t_ms": 7400,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.85,
        "eye_size": 1.05,
        "pupil": 1.1,
        "sparkle": 1,
        "look_x": 0.2,
        "look_y": -0.5,
        "brow_show": true,
        "brow_left": -2,
        "brow_right": 6,
        "brow_height": 0.3,
        "mouth": "pout",
        "mouth_open": 0.5,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": -4,
        "head_pan": -6,
        "head_tilt": 12,
        "ear_left": 0.9,
        "ear_right": 0.9,
        "ms": 1000
      }
    },
    {
      "t_ms": 8400,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.85,
        "eye_size": 1.05,
        "pupil": 1.1,
        "sparkle": 1,
        "look_x": -0.3,
        "look_y": 0.2,
        "brow_show": true,
        "brow_left": -2,
        "brow_right": 6,
        "brow_height": 0.3,
        "mouth": "pout",
        "mouth_open": 0.3,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": -4,
        "head_pan": -2,
        "head_tilt": 8,
        "ear_left": 0.9,
        "ear_right": 0.9,
        "ms": 1000
      }
    },
    {
      "t_ms": 9400,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.85,
        "eye_size": 1.05,
        "pupil": 1.1,
        "sparkle": 1,
        "look_x": 0.35,
        "look_y": -0.55,
        "brow_show": true,
        "brow_left": -2,
        "brow_right": 6,
        "brow_height": 0.3,
        "mouth": "pout",
        "mouth_open": 0.55,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": -4,
        "head_pan": 6,
        "head_tilt": 12,
        "ear_left": 1,
        "ear_right": 0.8,
        "ms": 1000
      }
    },
    {
      "t_ms": 10400,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.85,
        "eye_size": 1.05,
        "pupil": 1.1,
        "sparkle": 1,
        "look_x": -0.2,
        "look_y": 0.15,
        "brow_show": true,
        "brow_left": -2,
        "brow_right": 6,
        "brow_height": 0.3,
        "mouth": "pout",
        "mouth_open": 0.35,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": -4,
        "head_pan": 0,
        "head_tilt": 5,
        "ear_left": 1,
        "ear_right": 0.8,
        "ms": 1000
      }
    },
    {
      "t_ms": 11800,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.85,
        "eye_size": 1.05,
        "pupil": 1.1,
        "sparkle": 1,
        "look_x": 0.5,
        "look_y": -0.1,
        "brow_show": true,
        "brow_left": -2,
        "brow_right": 6,
        "brow_height": 0.3,
        "mouth": "pout",
        "mouth_open": 0.35,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 4,
        "head_pan": 15,
        "head_tilt": 5,
        "ear_left": 1,
        "ear_right": 0.9,
        "ms": 1400
      }
    },
    {
      "t_ms": 13400,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.55,
        "eye_size": 1.05,
        "pupil": 1.1,
        "sparkle": 0.5,
        "look_x": 0.5,
        "look_y": 0.3,
        "brow_show": true,
        "brow_left": -2,
        "brow_right": 6,
        "brow_height": 0.3,
        "mouth": "smile",
        "mouth_open": 0.1,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 4,
        "head_pan": 15,
        "head_tilt": -6,
        "ear_left": 0.6,
        "ear_right": 0.6,
        "ms": 1600
      }
    },
    {
      "t_ms": 14500,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.55,
        "eye_size": 1,
        "pupil": 0.9,
        "sparkle": 0.5,
        "look_x": 0,
        "look_y": 0.3,
        "brow_show": true,
        "brow_left": 0,
        "brow_right": 0,
        "brow_height": 0,
        "mouth": "smile",
        "mouth_open": 0.1,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": false,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2b2a33",
          "iris": "#6b4a3a",
          "blush": "#f09aa6",
          "tear": "#5dade2",
          "face_bg": "#fbf8f3",
          "head": "#8e929c"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 0,
        "head_tilt": -6,
        "ear_left": 0.6,
        "ear_right": 0.6,
        "ms": 1100
      }
    },
    {
      "t_ms": 14800,
      "ease": "bounce",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.7,
        "eye_size": 1.05,
        "pupil": 1.1,
        "sparkle": 0.5,
        "look_x": 0.5,
        "look_y": 0.3,
        "brow_show": true,
        "brow_left": -2,
        "brow_right": 6,
        "brow_height": 0.3,
        "mouth": "smile",
        "mouth_open": 0.1,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 4,
        "head_pan": 0,
        "head_tilt": -6,
        "ear_left": 1,
        "ear_right": 0.6,
        "ms": 300
      }
    },
    {
      "t_ms": 15300,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.9,
        "eye_size": 1,
        "pupil": 0.9,
        "sparkle": 0.8,
        "look_x": 0,
        "look_y": 0,
        "brow_show": true,
        "brow_left": 0,
        "brow_right": 0,
        "brow_height": 0,
        "mouth": "y",
        "mouth_open": 0.25,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": false,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2b2a33",
          "iris": "#6b4a3a",
          "blush": "#f09aa6",
          "tear": "#5dade2",
          "face_bg": "#fbf8f3",
          "head": "#8e929c"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 0,
        "head_tilt": 0,
        "ear_left": 1,
        "ear_right": 0.6,
        "ms": 500
      }
    },
    {
      "t_ms": 15800,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.9,
        "eye_size": 1,
        "pupil": 0.9,
        "sparkle": 0.8,
        "look_x": 0,
        "look_y": 0,
        "brow_show": true,
        "brow_left": 0,
        "brow_right": 0,
        "brow_height": 0,
        "mouth": "y",
        "mouth_open": 0.25,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": false,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 0,
        "head_tilt": 0,
        "ear_left": 1,
        "ear_right": 1,
        "ms": 500
      }
    }
  ]
})json";

const char IM_SO_BOORED_JSON[] = R"json({
  "format": "C3-taslak",
  "name": "adsız klip",
  "emotion": "idle",
  "loop": false,
  "duration_ms": 14800,
  "keys": [
    {
      "t_ms": 0,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.9,
        "eye_size": 1,
        "pupil": 0.9,
        "sparkle": 0.8,
        "look_x": 0,
        "look_y": 0,
        "brow_show": true,
        "brow_left": 0,
        "brow_right": 0,
        "brow_height": 0,
        "mouth": "y",
        "mouth_open": 0.25,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": false,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 0,
        "head_tilt": 0,
        "ear_left": 1,
        "ear_right": 1,
        "ms": 0
      }
    },
    {
      "t_ms": 1500,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.9,
        "eye_size": 1.15,
        "pupil": 0.9,
        "sparkle": 1,
        "look_x": 0,
        "look_y": 0,
        "brow_show": true,
        "brow_left": 7,
        "brow_right": 7,
        "brow_height": 0.3,
        "mouth": "smile",
        "mouth_open": 0.25,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": false,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 0,
        "head_tilt": 8,
        "ear_left": 1,
        "ear_right": 1,
        "ms": 1500
      }
    },
    {
      "t_ms": 3000,
      "ease": "stop",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.8,
        "eye_size": 1,
        "pupil": 0.9,
        "sparkle": 0.6,
        "look_x": 0,
        "look_y": 0.1,
        "brow_show": true,
        "brow_left": 10,
        "brow_right": 10,
        "brow_height": 0,
        "mouth": "flat",
        "mouth_open": 0,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": false,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 0,
        "head_tilt": 0,
        "ear_left": 0.7,
        "ear_right": 0.7,
        "ms": 1500
      }
    },
    {
      "t_ms": 4500,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.8,
        "eye_size": 1.15,
        "pupil": 0.8,
        "sparkle": 0.7,
        "look_x": 0.45,
        "look_y": 0.1,
        "brow_show": true,
        "brow_left": -18,
        "brow_right": -18,
        "brow_height": 0,
        "mouth": "frown",
        "mouth_open": 0.4,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": true,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": -8,
        "head_pan": -18,
        "head_tilt": 10,
        "ear_left": 0.3,
        "ear_right": 0.3,
        "ms": 1500
      }
    },
    {
      "t_ms": 6000,
      "ease": "bounce",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.6,
        "eye_size": 1.15,
        "pupil": 0.8,
        "sparkle": 0.7,
        "look_x": -0.6,
        "look_y": 0.1,
        "brow_show": true,
        "brow_left": -22,
        "brow_right": -22,
        "brow_height": 0,
        "mouth": "frown",
        "mouth_open": 0.4,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "gloom": 0,
        "rage": 0.25,
        "anger_mark": true,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": -12,
        "head_pan": -28,
        "head_tilt": 10,
        "ear_left": 0.15,
        "ear_right": 0.15,
        "ms": 1500
      }
    },
    {
      "t_ms": 7500,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.85,
        "eye_size": 1.15,
        "pupil": 0.8,
        "sparkle": 0.7,
        "look_x": 0.7,
        "look_y": 0.1,
        "brow_show": true,
        "brow_left": -10,
        "brow_right": -10,
        "brow_height": 0,
        "mouth": "frown",
        "mouth_open": 0.3,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": -12,
        "head_pan": -28,
        "head_tilt": 10,
        "ear_left": 0.35,
        "ear_right": 0.7,
        "ms": 1500
      }
    },
    {
      "t_ms": 9000,
      "ease": "smooth",
      "face": {
        "eye_shape": "closed",
        "eye_open": 0.85,
        "eye_size": 1.15,
        "pupil": 0.8,
        "sparkle": 0.7,
        "look_x": 0.7,
        "look_y": 0.1,
        "brow_show": true,
        "brow_left": -15,
        "brow_right": -15,
        "brow_height": 0,
        "mouth": "frown",
        "mouth_open": 0.6,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": -8,
        "head_pan": -20,
        "head_tilt": 18,
        "ear_left": 0.2,
        "ear_right": 0.2,
        "ms": 1500
      }
    },
    {
      "t_ms": 10500,
      "ease": "stop",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.85,
        "eye_size": 1.2,
        "pupil": 1.05,
        "sparkle": 1,
        "look_x": 0.3,
        "look_y": 0.25,
        "brow_show": true,
        "brow_left": 14,
        "brow_right": 14,
        "brow_height": 0.2,
        "mouth": "zigzag",
        "mouth_open": 0.35,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0.35,
        "blush": true,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": -10,
        "head_tilt": 6,
        "ear_left": 0.4,
        "ear_right": 0.4,
        "ms": 1500
      }
    },
    {
      "t_ms": 12000,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.85,
        "eye_size": 1.3,
        "pupil": 1.1,
        "sparkle": 1,
        "look_x": 0,
        "look_y": -0.2,
        "brow_show": true,
        "brow_left": 24,
        "brow_right": 24,
        "brow_height": 0.2,
        "mouth": "wavy",
        "mouth_open": 0.25,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0.55,
        "blush": true,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 0,
        "head_tilt": 8,
        "ear_left": 0.15,
        "ear_right": 0.15,
        "ms": 1500
      }
    },
    {
      "t_ms": 13500,
      "ease": "stop",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.85,
        "eye_size": 1.2,
        "pupil": 1.05,
        "sparkle": 1,
        "look_x": 0,
        "look_y": -0.15,
        "brow_show": true,
        "brow_left": 18,
        "brow_right": 18,
        "brow_height": 0.2,
        "mouth": "wavy",
        "mouth_open": 0.2,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0.5,
        "blush": true,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 0,
        "head_tilt": 6,
        "ear_left": 0.35,
        "ear_right": 0.35,
        "ms": 1500
      }
    },
    {
      "t_ms": 14800,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.85,
        "eye_size": 1.2,
        "pupil": 1.05,
        "sparkle": 1,
        "look_x": 0,
        "look_y": -0.15,
        "brow_show": true,
        "brow_left": 18,
        "brow_right": 18,
        "brow_height": 0.2,
        "mouth": "wavy",
        "mouth_open": 0.2,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0.5,
        "blush": true,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 0,
        "head_tilt": 6,
        "ear_left": 0.35,
        "ear_right": 0.35,
        "ms": 1300
      }
    }
  ]
})json";

const char PLAYFUL_JSON[] = R"json({
  "format": "C3-taslak",
  "name": "Yakalandık",
  "emotion": "playful",
  "loop": false,
  "duration_ms": 4420,
  "keys": [
    {
      "t_ms": 40,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.9,
        "eye_size": 1.1,
        "pupil": 0.9,
        "sparkle": 1,
        "look_x": -0.75,
        "look_y": -0.9,
        "brow_show": true,
        "brow_left": 3,
        "brow_right": 3,
        "brow_height": 0.4,
        "mouth": "smile",
        "mouth_open": 1,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": -10,
        "head_pan": -25,
        "head_tilt": 10,
        "ear_left": 0.86,
        "ear_right": 0.86,
        "ms": 40
      }
    },
    {
      "t_ms": 880,
      "ease": "bounce",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.9,
        "eye_size": 1.1,
        "pupil": 0.9,
        "sparkle": 1,
        "look_x": -0.92,
        "look_y": 0.77,
        "brow_show": true,
        "brow_left": 3,
        "brow_right": 3,
        "brow_height": 0.4,
        "mouth": "w",
        "mouth_open": 1,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": -10,
        "head_pan": -25,
        "head_tilt": 10,
        "ear_left": 0.86,
        "ear_right": 0.86,
        "ms": 840
      }
    },
    {
      "t_ms": 1570,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.9,
        "eye_size": 1.1,
        "pupil": 0.9,
        "sparkle": 1,
        "look_x": -0.02,
        "look_y": 1,
        "brow_show": true,
        "brow_left": 3,
        "brow_right": 3,
        "brow_height": 0.4,
        "mouth": "w",
        "mouth_open": 1,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": -10,
        "head_pan": -25,
        "head_tilt": 10,
        "ear_left": 0.86,
        "ear_right": 0.86,
        "ms": 690
      }
    },
    {
      "t_ms": 2240,
      "ease": "bounce",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.9,
        "eye_size": 1.1,
        "pupil": 0.9,
        "sparkle": 1,
        "look_x": 1,
        "look_y": 1,
        "brow_show": true,
        "brow_left": 3,
        "brow_right": 3,
        "brow_height": 0.4,
        "mouth": "w",
        "mouth_open": 1,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": -10,
        "head_pan": -25,
        "head_tilt": 10,
        "ear_left": 0.86,
        "ear_right": 0.86,
        "ms": 670
      }
    },
    {
      "t_ms": 2880,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.9,
        "eye_size": 1.1,
        "pupil": 0.9,
        "sparkle": 1,
        "look_x": 1,
        "look_y": -0.36,
        "brow_show": true,
        "brow_left": 3,
        "brow_right": 3,
        "brow_height": 0.4,
        "mouth": "w",
        "mouth_open": 1,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "colors": {
          "line": "#2b2a33",
          "iris": "#6b4a3a",
          "blush": "#f09aa6",
          "tear": "#5dade2",
          "face_bg": "#fbf8f3",
          "head": "#8e929c"
        }
      },
      "pose": {
        "body_yaw": -10,
        "head_pan": -25,
        "head_tilt": 10,
        "ear_left": 0.86,
        "ear_right": 0.86,
        "ms": 640
      }
    },
    {
      "t_ms": 3580,
      "ease": "bounce",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.9,
        "eye_size": 1.1,
        "pupil": 0.9,
        "sparkle": 1,
        "look_x": 0,
        "look_y": -0.97,
        "brow_show": true,
        "brow_left": 3,
        "brow_right": 3,
        "brow_height": 0.4,
        "mouth": "w",
        "mouth_open": 0,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": -10,
        "head_pan": -25,
        "head_tilt": 10,
        "ear_left": 0.86,
        "ear_right": 0.86,
        "ms": 700
      }
    },
    {
      "t_ms": 4420,
      "ease": "stop",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.9,
        "eye_size": 1.1,
        "pupil": 0.9,
        "sparkle": 1,
        "look_x": 0.2,
        "look_y": -1,
        "brow_show": true,
        "brow_left": 6,
        "brow_right": 9,
        "brow_height": 0.56,
        "mouth": "smile",
        "mouth_open": 1,
        "tears": 0,
        "blush": true,
        "sweat": true,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": -10,
        "head_pan": -25,
        "head_tilt": 10,
        "ear_left": 0.67,
        "ear_right": 0.67,
        "ms": 840
      }
    }
  ]
})json";

const char SAD_JSON[] = R"json({
  "format": "C3-taslak",
  "name": "adsız klip",
  "emotion": "sad",
  "loop": false,
  "duration_ms": 2380,
  "keys": [
    {
      "t_ms": 0,
      "ease": "smooth",
      "face": {
        "eye_shape": "arc",
        "eye_open": 0.9,
        "eye_size": 1,
        "pupil": 0.9,
        "sparkle": 0.8,
        "look_x": 0,
        "look_y": 0,
        "brow_show": false,
        "brow_left": 0,
        "brow_right": 0,
        "brow_height": 0,
        "mouth": "w",
        "mouth_open": 0.6,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 0,
        "head_tilt": 8,
        "ear_left": 1,
        "ear_right": 1,
        "ms": 0
      }
    },
    {
      "t_ms": 350,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.9,
        "eye_size": 1,
        "pupil": 0.9,
        "sparkle": 0.8,
        "look_x": 0,
        "look_y": 0,
        "brow_show": true,
        "brow_left": 0,
        "brow_right": 0,
        "brow_height": 0.34,
        "mouth": "w",
        "mouth_open": 0,
        "tears": 0,
        "blush": false,
        "sweat": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 0,
        "head_tilt": 0,
        "ear_left": 0.86,
        "ear_right": 0.86,
        "ms": 350
      }
    },
    {
      "t_ms": 780,
      "ease": "snap",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.9,
        "eye_size": 1,
        "pupil": 0.9,
        "sparkle": 0.8,
        "look_x": 0,
        "look_y": 0,
        "brow_show": true,
        "brow_left": 0,
        "brow_right": 0,
        "brow_height": 0.34,
        "mouth": "flat",
        "mouth_open": 0,
        "tears": 0,
        "blush": false,
        "sweat": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 0,
        "head_tilt": 0,
        "ear_left": 1,
        "ear_right": 1,
        "ms": 430
      }
    },
    {
      "t_ms": 1180,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.9,
        "eye_size": 1.18,
        "pupil": 0.85,
        "sparkle": 0.8,
        "look_x": 0,
        "look_y": 0,
        "brow_show": true,
        "brow_left": 0,
        "brow_right": 0,
        "brow_height": 0.34,
        "mouth": "flat",
        "mouth_open": 0,
        "tears": 0,
        "blush": false,
        "sweat": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 0,
        "head_tilt": 0,
        "ear_left": 1,
        "ear_right": 1,
        "ms": 400
      }
    },
    {
      "t_ms": 1540,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.9,
        "eye_size": 1.18,
        "pupil": 1,
        "sparkle": 0.8,
        "look_x": 0,
        "look_y": 0,
        "brow_show": true,
        "brow_left": 16,
        "brow_right": 16,
        "brow_height": 0.34,
        "mouth": "wavy",
        "mouth_open": 0.5,
        "tears": 0,
        "blush": false,
        "sweat": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 0,
        "head_tilt": 0,
        "ear_left": 0.69,
        "ear_right": 0.69,
        "ms": 360
      }
    },
    {
      "t_ms": 1910,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.9,
        "eye_size": 1.18,
        "pupil": 1,
        "sparkle": 0.8,
        "look_x": 0,
        "look_y": 0,
        "brow_show": true,
        "brow_left": 16,
        "brow_right": 16,
        "brow_height": 0.34,
        "mouth": "wavy",
        "mouth_open": 0.5,
        "tears": 0.43,
        "blush": true,
        "sweat": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 0,
        "head_tilt": 0,
        "ear_left": 0.69,
        "ear_right": 0.69,
        "ms": 370
      }
    },
    {
      "t_ms": 2380,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.9,
        "eye_size": 1.18,
        "pupil": 1,
        "sparkle": 0.8,
        "look_x": 0,
        "look_y": 0,
        "brow_show": true,
        "brow_left": 16,
        "brow_right": 16,
        "brow_height": 0.34,
        "mouth": "wavy",
        "mouth_open": 1,
        "tears": 1,
        "blush": true,
        "sweat": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 0,
        "head_tilt": 0,
        "ear_left": 0.69,
        "ear_right": 0.69,
        "ms": 470
      }
    }
  ]
})json";

const char SLEEPY_JSON[] = R"json({
  "format": "C3-taslak",
  "name": "esneme(yorgunluk)",
  "emotion": "sleepy",
  "loop": false,
  "duration_ms": 3010,
  "keys": [
    {
      "t_ms": 0,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.45,
        "eye_size": 1,
        "pupil": 0.9,
        "sparkle": 0,
        "look_x": 0,
        "look_y": 0.3,
        "brow_show": false,
        "brow_left": 0,
        "brow_right": 0,
        "brow_height": 0,
        "mouth": "flat",
        "mouth_open": 0,
        "tears": 0,
        "blush": false,
        "sweat": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": -5,
        "head_tilt": 0,
        "ear_left": 0.5,
        "ear_right": 0.5,
        "ms": 0
      }
    },
    {
      "t_ms": 700,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.45,
        "eye_size": 1,
        "pupil": 0.9,
        "sparkle": 0,
        "look_x": 0.06,
        "look_y": 0.1,
        "brow_show": false,
        "brow_left": 0,
        "brow_right": 0,
        "brow_height": 0,
        "mouth": "flat",
        "mouth_open": 0,
        "tears": 0,
        "blush": false,
        "sweat": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 20,
        "head_tilt": 0,
        "ear_left": 0.5,
        "ear_right": 0.5,
        "ms": 700
      }
    },
    {
      "t_ms": 1400,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.45,
        "eye_size": 1,
        "pupil": 0.9,
        "sparkle": 0,
        "look_x": -0.6,
        "look_y": 0.1,
        "brow_show": false,
        "brow_left": 0,
        "brow_right": 0,
        "brow_height": 0,
        "mouth": "flat",
        "mouth_open": 0,
        "tears": 0,
        "blush": false,
        "sweat": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": -20,
        "head_tilt": 0,
        "ear_left": 0.5,
        "ear_right": 0.5,
        "ms": 700
      }
    },
    {
      "t_ms": 2000,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.25,
        "eye_size": 1,
        "pupil": 0.9,
        "sparkle": 0,
        "look_x": -0.6,
        "look_y": 0.4,
        "brow_show": false,
        "brow_left": 0,
        "brow_right": 0,
        "brow_height": 0,
        "mouth": "o",
        "mouth_open": 0.3,
        "tears": 0,
        "blush": false,
        "sweat": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": -20,
        "head_tilt": -10,
        "ear_left": 0.3,
        "ear_right": 0.3,
        "ms": 600
      }
    },
    {
      "t_ms": 2500,
      "ease": "bounce",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.1,
        "eye_size": 1,
        "pupil": 0.9,
        "sparkle": 0,
        "look_x": -0.6,
        "look_y": 0.4,
        "brow_show": false,
        "brow_left": 0,
        "brow_right": 0,
        "brow_height": 0,
        "mouth": "o",
        "mouth_open": 1,
        "tears": 0,
        "blush": false,
        "sweat": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": -20,
        "head_tilt": 10,
        "ear_left": 0.7,
        "ear_right": 0.7,
        "ms": 500
      }
    },
    {
      "t_ms": 3010,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.45,
        "eye_size": 1,
        "pupil": 0.9,
        "sparkle": 0,
        "look_x": -0.6,
        "look_y": 0.3,
        "brow_show": false,
        "brow_left": 0,
        "brow_right": 0,
        "brow_height": 0,
        "mouth": "flat",
        "mouth_open": 0,
        "tears": 0,
        "blush": false,
        "sweat": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": -20,
        "head_tilt": -5,
        "ear_left": 0.5,
        "ear_right": 0.5,
        "ms": 510
      }
    }
  ]
})json";

const char SMILE_JSON[] = R"json({
  "format": "C3-taslak",
  "name": "adsız klip",
  "emotion": "idle",
  "loop": false,
  "duration_ms": 10500,
  "keys": [
    {
      "t_ms": 0,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.9,
        "eye_size": 1,
        "pupil": 0.9,
        "sparkle": 0.8,
        "look_x": 0,
        "look_y": 0,
        "brow_show": true,
        "brow_left": 0,
        "brow_right": 0,
        "brow_height": 0,
        "mouth": "y",
        "mouth_open": 0.25,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": false,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 0,
        "head_tilt": 0,
        "ear_left": 1,
        "ear_right": 1,
        "ms": 0
      }
    },
    {
      "t_ms": 1500,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.9,
        "eye_size": 1.05,
        "pupil": 0.9,
        "sparkle": 1,
        "look_x": 0,
        "look_y": 0,
        "brow_show": true,
        "brow_left": 0,
        "brow_right": 0,
        "brow_height": 0,
        "mouth": "smile",
        "mouth_open": 0.3,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": false,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 0,
        "head_tilt": 3,
        "ear_left": 0.9,
        "ear_right": 0.9,
        "ms": 1500
      }
    },
    {
      "t_ms": 3000,
      "ease": "stop",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.9,
        "eye_size": 1.1,
        "pupil": 1,
        "sparkle": 1,
        "look_x": 0,
        "look_y": 0,
        "brow_show": true,
        "brow_left": 0,
        "brow_right": 0,
        "brow_height": 0,
        "mouth": "smile",
        "mouth_open": 0.55,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 6,
        "head_tilt": 6,
        "ear_left": 0.9,
        "ear_right": 0.9,
        "ms": 1500
      }
    },
    {
      "t_ms": 4500,
      "ease": "smooth",
      "face": {
        "eye_shape": "arc",
        "eye_open": 0.9,
        "eye_size": 1,
        "pupil": 0.9,
        "sparkle": 0.8,
        "look_x": 0,
        "look_y": 0,
        "brow_show": false,
        "brow_left": 0,
        "brow_right": 0,
        "brow_height": 0,
        "mouth": "w",
        "mouth_open": 0.6,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": -6,
        "head_tilt": 8,
        "ear_left": 1,
        "ear_right": 1,
        "ms": 1500
      }
    },
    {
      "t_ms": 6000,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.9,
        "eye_size": 1.1,
        "pupil": 0.9,
        "sparkle": 1,
        "look_x": 0.35,
        "look_y": 0.1,
        "brow_show": false,
        "brow_left": 0,
        "brow_right": 0,
        "brow_height": 0,
        "mouth": "smile",
        "mouth_open": 0.45,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 4,
        "head_pan": 12,
        "head_tilt": 8,
        "ear_left": 1,
        "ear_right": 0.8,
        "ms": 1500
      }
    },
    {
      "t_ms": 7500,
      "ease": "smooth",
      "face": {
        "eye_shape": "arc",
        "eye_open": 0.9,
        "eye_size": 1,
        "pupil": 0.9,
        "sparkle": 0.8,
        "look_x": 0,
        "look_y": 0,
        "brow_show": false,
        "brow_left": 0,
        "brow_right": 0,
        "brow_height": 0,
        "mouth": "w",
        "mouth_open": 0.5,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 0,
        "head_tilt": 10,
        "ear_left": 1,
        "ear_right": 1,
        "ms": 1500
      }
    },
    {
      "t_ms": 9000,
      "ease": "stop",
      "face": {
        "eye_shape": "closed",
        "eye_open": 0.9,
        "eye_size": 1,
        "pupil": 0.9,
        "sparkle": 0.8,
        "look_x": 0,
        "look_y": 0,
        "brow_show": false,
        "brow_left": 0,
        "brow_right": 0,
        "brow_height": 0,
        "mouth": "smile",
        "mouth_open": 0.6,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 0,
        "head_tilt": 4,
        "ear_left": 0.8,
        "ear_right": 0.8,
        "ms": 1500
      }
    },
    {
      "t_ms": 10500,
      "ease": "smooth",
      "face": {
        "eye_shape": "closed",
        "eye_open": 0.9,
        "eye_size": 1,
        "pupil": 0.9,
        "sparkle": 0.8,
        "look_x": 0,
        "look_y": 0,
        "brow_show": false,
        "brow_left": 0,
        "brow_right": 0,
        "brow_height": 0,
        "mouth": "smile",
        "mouth_open": 0.6,
        "mouth_width": 1,
        "mouth_x": 0,
        "mouth_tilt": 0,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "gloom": 0,
        "rage": 0,
        "anger_mark": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 0,
        "head_tilt": 4,
        "ear_left": 0.8,
        "ear_right": 0.8,
        "ms": 1500
      }
    }
  ]
})json";

const char STARTLED_JSON[] = R"json({
  "format": "C3-taslak",
  "name": "irkilme",
  "emotion": "startled",
  "loop": false,
  "duration_ms": 3370,
  "keys": [
    {
      "t_ms": 0,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.9,
        "eye_size": 1,
        "pupil": 0.9,
        "sparkle": 0.8,
        "look_x": 0,
        "look_y": 0,
        "brow_show": true,
        "brow_left": 0,
        "brow_right": 0,
        "brow_height": 0,
        "mouth": "y",
        "mouth_open": 0.25,
        "tears": 0,
        "blush": false,
        "sweat": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 0,
        "head_tilt": 0,
        "ear_left": 1,
        "ear_right": 1,
        "ms": 0
      }
    },
    {
      "t_ms": 880,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.6,
        "eye_size": 1,
        "pupil": 0.9,
        "sparkle": 0.8,
        "look_x": 0,
        "look_y": 0,
        "brow_show": true,
        "brow_left": 0,
        "brow_right": 0,
        "brow_height": 0,
        "mouth": "flat",
        "mouth_open": 0.25,
        "tears": 0,
        "blush": false,
        "sweat": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 0,
        "head_tilt": -6,
        "ear_left": 0.8,
        "ear_right": 0.8,
        "ms": 880
      }
    },
    {
      "t_ms": 1010,
      "ease": "snap",
      "face": {
        "eye_shape": "round",
        "eye_open": 1,
        "eye_size": 1.4,
        "pupil": 0.5,
        "sparkle": 0.3,
        "look_x": 0,
        "look_y": 0,
        "brow_show": true,
        "brow_left": -6,
        "brow_right": -6,
        "brow_height": 1,
        "mouth": "o",
        "mouth_open": 1,
        "tears": 0,
        "blush": false,
        "sweat": true,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 0,
        "head_tilt": 20,
        "ear_left": 1,
        "ear_right": 1,
        "ms": 130
      }
    },
    {
      "t_ms": 1710,
      "ease": "linear",
      "face": {
        "eye_shape": "round",
        "eye_open": 1,
        "eye_size": 1.4,
        "pupil": 0.5,
        "sparkle": 0.3,
        "look_x": -1,
        "look_y": 0,
        "brow_show": true,
        "brow_left": -6,
        "brow_right": -6,
        "brow_height": 1,
        "mouth": "o",
        "mouth_open": 1,
        "tears": 0,
        "blush": false,
        "sweat": true,
        "colors": {
          "line": "#2b2a33",
          "iris": "#6b4a3a",
          "blush": "#f09aa6",
          "tear": "#5dade2",
          "face_bg": "#fbf8f3",
          "head": "#8e929c"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 0,
        "head_tilt": 20,
        "ear_left": 1,
        "ear_right": 1,
        "ms": 700
      }
    },
    {
      "t_ms": 2060,
      "ease": "linear",
      "face": {
        "eye_shape": "round",
        "eye_open": 1,
        "eye_size": 1.4,
        "pupil": 0.5,
        "sparkle": 0.3,
        "look_x": 0.96,
        "look_y": 0,
        "brow_show": true,
        "brow_left": -6,
        "brow_right": -6,
        "brow_height": 1,
        "mouth": "o",
        "mouth_open": 1,
        "tears": 0,
        "blush": false,
        "sweat": true,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 0,
        "head_tilt": 20,
        "ear_left": 1,
        "ear_right": 1,
        "ms": 350
      }
    },
    {
      "t_ms": 2770,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.9,
        "eye_size": 1,
        "pupil": 0.9,
        "sparkle": 0.8,
        "look_x": 0.3,
        "look_y": 0,
        "brow_show": true,
        "brow_left": 0,
        "brow_right": 0,
        "brow_height": 0,
        "mouth": "y",
        "mouth_open": 0.25,
        "tears": 0,
        "blush": false,
        "sweat": true,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 0,
        "head_tilt": 0,
        "ear_left": 0.85,
        "ear_right": 0.85,
        "ms": 710
      }
    },
    {
      "t_ms": 3370,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.9,
        "eye_size": 1,
        "pupil": 0.9,
        "sparkle": 0.8,
        "look_x": 0,
        "look_y": 0,
        "brow_show": true,
        "brow_left": 0,
        "brow_right": 0,
        "brow_height": 0,
        "mouth": "y",
        "mouth_open": 0.25,
        "tears": 0,
        "blush": false,
        "sweat": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 0,
        "head_tilt": 0,
        "ear_left": 1,
        "ear_right": 1,
        "ms": 600
      }
    }
  ]
})json";

const char TSUNDERE_JSON[] = R"json({
  "format": "C3-taslak",
  "name": "Tsundere",
  "emotion": "idle",
  "loop": false,
  "duration_ms": 4200,
  "keys": [
    {
      "t_ms": 0,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.9,
        "eye_size": 1,
        "pupil": 0.9,
        "sparkle": 0.8,
        "look_x": 0,
        "look_y": 0,
        "brow_show": true,
        "brow_left": 0,
        "brow_right": 0,
        "brow_height": 0,
        "mouth": "y",
        "mouth_open": 0.25,
        "tears": 0,
        "blush": false,
        "sweat": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 0,
        "head_tilt": 0,
        "ear_left": 1,
        "ear_right": 1,
        "ms": 0
      }
    },
    {
      "t_ms": 900,
      "ease": "stop",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.85,
        "eye_size": 1.15,
        "pupil": 0.9,
        "sparkle": 0.7,
        "look_x": 0.45,
        "look_y": 0.1,
        "brow_show": true,
        "brow_left": -10,
        "brow_right": -10,
        "brow_height": -0.2,
        "mouth": "wavy",
        "mouth_open": 0.2,
        "tears": 0.15,
        "blush": true,
        "sweat": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": -8,
        "head_pan": -18,
        "head_tilt": 10,
        "ear_left": 0.3,
        "ear_right": 0.3,
        "ms": 900
      }
    },
    {
      "t_ms": 1700,
      "ease": "bounce",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.85,
        "eye_size": 1.2,
        "pupil": 0.8,
        "sparkle": 0.7,
        "look_x": 0.45,
        "look_y": 0.1,
        "brow_show": true,
        "brow_left": -24,
        "brow_right": -24,
        "brow_height": -0.2,
        "mouth": "wavy",
        "mouth_open": 0.45,
        "tears": 0.15,
        "blush": true,
        "sweat": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": -8,
        "head_pan": -18,
        "head_tilt": 14,
        "ear_left": 0.2,
        "ear_right": 0.2,
        "ms": 800
      }
    },
    {
      "t_ms": 2400,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.85,
        "eye_size": 1.2,
        "pupil": 0.8,
        "sparkle": 0.7,
        "look_x": -0.45,
        "look_y": 0.1,
        "brow_show": true,
        "brow_left": -24,
        "brow_right": -24,
        "brow_height": -0.2,
        "mouth": "wavy",
        "mouth_open": 0.45,
        "tears": 0.15,
        "blush": true,
        "sweat": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 8,
        "head_pan": 18,
        "head_tilt": 14,
        "ear_left": 0.2,
        "ear_right": 0.2,
        "ms": 700
      }
    },
    {
      "t_ms": 3200,
      "ease": "smooth",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.85,
        "eye_size": 1.2,
        "pupil": 0.9,
        "sparkle": 0.7,
        "look_x": -0.45,
        "look_y": 0.1,
        "brow_show": true,
        "brow_left": -18,
        "brow_right": -18,
        "brow_height": -0.2,
        "mouth": "wavy",
        "mouth_open": 0.45,
        "tears": 0.15,
        "blush": true,
        "sweat": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 8,
        "head_pan": 18,
        "head_tilt": 14,
        "ear_left": 0.2,
        "ear_right": 0.2,
        "ms": 800
      }
    },
    {
      "t_ms": 4200,
      "ease": "bounce",
      "face": {
        "eye_shape": "round",
        "eye_open": 0.8,
        "eye_size": 1.1,
        "pupil": 0.9,
        "sparkle": 0.8,
        "look_x": 0.2,
        "look_y": 0.25,
        "brow_show": true,
        "brow_left": -5,
        "brow_right": -5,
        "brow_height": 0,
        "mouth": "wavy",
        "mouth_open": 0.2,
        "tears": 0,
        "blush": true,
        "sweat": false,
        "colors": {
          "line": "#2B2A33",
          "iris": "#6B4A3A",
          "blush": "#F09AA6",
          "tear": "#5DADE2",
          "face_bg": "#FBF8F3",
          "head": "#8E929C"
        }
      },
      "pose": {
        "body_yaw": 0,
        "head_pan": 8,
        "head_tilt": 2,
        "ear_left": 0.6,
        "ear_right": 0.6,
        "ms": 1000
      }
    }
  ]
})json";

// klip listesi, yeni klip eklenirse otomatik güncellenir
const Klip klipler[] = {
    {"curious", CURIOUS_JSON},
    {"curious2", CURIOUS2_JSON},
    {"happy", HAPPY_JSON},
    {"head_explosion_buum", HEAD_EXPLOSION_BUUM_JSON},
    {"idle", IDLE_JSON},
    {"im_so_boored", IM_SO_BOORED_JSON},
    {"playful", PLAYFUL_JSON},
    {"sad", SAD_JSON},
    {"sleepy", SLEEPY_JSON},
    {"smile", SMILE_JSON},
    {"startled", STARTLED_JSON},
    {"tsundere", TSUNDERE_JSON}
};

const int KLIP_SAYISI = sizeof(klipler) / sizeof(klipler[0]);
