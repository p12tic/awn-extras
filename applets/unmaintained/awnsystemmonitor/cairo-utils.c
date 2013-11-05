/*
 *  Copyright (C) 2007 Anthony Arobone <aarobone@gmail.com>
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, write to the
 * Free Software Foundation, Inc., 59 Temple Place - Suite 330,
 * Boston, MA 02111-1307, USA.
 *
 *  Author : Anthony Arobone <aarobone@gmail.com>
*/


#include <gtk/gtk.h>

#include "cairo-utils.h"
static int
getdec(char hexchar)
{
  if ((hexchar >= '0') && (hexchar <= '9')) return hexchar - '0';

  if ((hexchar >= 'A') && (hexchar <= 'F')) return hexchar - 'A' + 10;

  if ((hexchar >= 'a') && (hexchar <= 'f')) return hexchar - 'a' + 10;

  return -1; // Wrong character

}

static void
hex2float(const char *HexColor, float *FloatColor)
{
  const char *HexColorPtr = HexColor;

  int i = 0;

  for (i = 0; i < 4; i++)
  {
    int IntColor = (getdec(HexColorPtr[0]) * 16) +
                   getdec(HexColorPtr[1]);

    FloatColor[i] = (float) IntColor / 255.0;
    HexColorPtr += 2;
  }

}

void
awn_cairo_string_to_color(const gchar *string, AwnColor *color)
{
  float colors[4];
  g_return_if_fail (string);
  g_return_if_fail (color);

  hex2float(string, colors);
  color->red = colors[0];
  color->green = colors[1];
  color->blue = colors[2];
  color->alpha = colors[3];
}

