#pragma once

struct Yuz
{
  bool gozKapali;
  float eye_open, eye_size, pupil, sparkle;
  float look_x, look_y;
  float brow_left, brow_right, brow_height;
  int mouth;
  float mouth_open, tears;
  bool blush, anger_mark;
};

// JSON içerisindeki servo pozları
struct Poz
{
  float body_yaw;
  float head_pan;
  float head_tilt;
  float ear_left;
  float ear_right;
};

struct Anahtar
{
  unsigned long t;
  int ease;
  Yuz yuz;
  Poz pose;
  bool poseVar;
};

struct Klip
{
  const char *ad;
  const char *json;
};