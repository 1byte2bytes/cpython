/* -*- C -*- ***********************************************
Copyright 1991-1995 by Stichting Mathematisch Centrum, Amsterdam,
The Netherlands.

                        All Rights Reserved

Permission to use, copy, modify, and distribute this software and its
documentation for any purpose and without fee is hereby granted,
provided that the above copyright notice appear in all copies and that
both that copyright notice and this permission notice appear in
supporting documentation, and that the names of Stichting Mathematisch
Centrum or CWI or Corporation for National Research Initiatives or
CNRI not be used in advertising or publicity pertaining to
distribution of the software without specific, written prior
permission.

While CWI is the initial source for this software, a modified version
is made available by the Corporation for National Research Initiatives
(CNRI) at the Internet address ftp://ftp.python.org.

STICHTING MATHEMATISCH CENTRUM AND CNRI DISCLAIM ALL WARRANTIES WITH
REGARD TO THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS, IN NO EVENT SHALL STICHTING MATHEMATISCH
CENTRUM OR CNRI BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL
DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR
PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER
TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
PERFORMANCE OF THIS SOFTWARE.

******************************************************************/

/* Module configuration */

/* This file contains the table of built-in modules.
   See init_builtin() in import.c. */

#include "Python.h"

extern void initarray();
extern void initaudioop();
extern void initbinascii();
extern void initcmath();
extern void initerrno();
extern void initimageop();
extern void initmath();
extern void initmd5();
extern void initnew();
extern void initnt();
extern void initoperator();
extern void initregex();
extern void initrgbimg();
extern void initrotor();
extern void initsignal();
extern void initsha();
extern void initselect();
extern void initsocket();
extern void initsoundex();
extern void initstrop();
extern void initstruct();
extern void inittime();
extern void initthread();
extern void initcStringIO();
extern void initcPickle();
extern void initpcre();
extern void initposix();
#ifdef WIN32
extern void initmsvcrt();
extern void initwinsound();
extern void init_locale();
#endif

/* -- ADDMODULE MARKER 1 -- */

extern void PyMarshal_Init();
extern void initimp();

struct _inittab _PyImport_Inittab[] = {
        //{"posix", initposix},
        {"array", initarray},
        {"binascii", initbinascii},
        {"cmath", initcmath},
        {"errno", initerrno},
        {"math", initmath},
        {"md5", initmd5},
        {"new", initnew},
        {"operator", initoperator},
        {"regex", initregex},
        {"rotor", initrotor},
        {"time", inittime},
        {"soundex", initsoundex},
        {"strop", initstrop},
        {"struct", initstruct},
        {"cStringIO", initcStringIO},
        {"cPickle", initcPickle},
        {"pcre", initpcre},
        {"_socket", initsocket},
        {"select", initselect},
        {"thread", initthread},
/*
        {"sha", initsha},
        {"imageop", initimageop},
        {"rgbimg", initrgbimg},
        {"signal", initsignal}, // This one breaks control+c in the terminal

#ifdef WIN32
	{"msvcrt", initmsvcrt},
	{"winsound", initwinsound},
	{"_locale", init_locale},
#endif

/* -- ADDMODULE MARKER 2 -- */

        /* This module "lives in" with marshal.c */
        {"marshal", PyMarshal_Init},

        /* This lives it with import.c */
        {"imp", initimp},

        /* These entries are here for sys.builtin_module_names */
        {"__main__", NULL},
        {"__builtin__", NULL},
        {"sys", NULL},

        /* Sentinel */
        {0, 0}
};
