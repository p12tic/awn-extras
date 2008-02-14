/*
 * 
 *
 * urlencdoe and urldecode Copyright (C) 2001-2002 Open Source Telecom Corporation.
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
 */

#include "awn-extras.h"

#include <ctype.h>

//urlencode:  Copyright (C) 2001-2002 Open Source Telecom Corporation.
char* urlencode(const char *source, char *dest, unsigned max)	
{
	static const char *hex = "0123456789abcdef";
	unsigned len = 0;
	unsigned char ch;
	char *ret = dest;

	while(len < max - 4 && *source)
	{
		ch = (unsigned char)*source;
		if(*source == ' ')
			*(dest++) = '+';
		else if(isalnum(*source) || *source == '/' || *source == '.')
			*(dest++) = *source;
		else
		{
			*(dest++) = '%';
			// char in C++ can be more than 8bit
			*(dest++) = hex[(ch >> 4)&0xF];
			*(dest++) = hex[ch % 16];
		}	
		++source;
	}
	*dest = 0;
	return ret;
}


//urldecode:  Copyright (C) 2001-2002 Open Source Telecom Corporation.
char *urldecode(char *source, char *dest)
{
	char *ret;
	if(!dest)
		dest = source;
	ret = dest;
	while(*source)
	{
		switch(*source)
		{
		case '+':
			*(dest++) = ' ';
			break;
		case '%':
			// NOTE: wrong input can finish with "...%" giving
			// buffer overflow, cut string here
			if ( !(dest[0] = source[1]) )
				return ret;
			if ( !(dest[1] = source[2]) )
				return ret;
			dest[2] = 0;
			*(dest++) = (char)strtol(dest, NULL, 16);
			source += 2;
			break;
		default:
			*(dest++) = *source;
		}
		++source;
	}
	*dest = 0;
	return ret;
}	
