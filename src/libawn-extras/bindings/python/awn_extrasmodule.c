/*
 * Copyright (c) 2007 Neil Jagdish Patel <njpatel@gmail.com>
 * Copyright (c) 2008 Mark Lee <avant-wn@lazymalevolence.com>
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

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <pygobject.h>
#include <cairo/cairo.h>
#include <pycairo.h>


void pyawn_extras_register_classes (PyObject *d);
extern PyMethodDef pyawn_extras_functions[];
static Pycairo_CAPI_t *Pycairo_CAPI;

DL_EXPORT (void)
init_extras (void)
{
        PyObject *m, *d;

        init_pygobject ();

        Pycairo_IMPORT;
        m = Py_InitModule ("_extras", pyawn_extras_functions);
        d = PyModule_GetDict (m);

        pyawn_extras_register_classes (d);

        if (PyErr_Occurred ()) {
                Py_FatalError ("unable to initialise awn._extras module");
        }
}

