/***********************************************************
Copyright 1991-1997 by Stichting Mathematisch Centrum, Amsterdam,
The Netherlands.

                        All Rights Reserved

Permission to use, copy, modify, and distribute this software and its 
documentation for any purpose and without fee is hereby granted, 
provided that the above copyright notice appear in all copies and that
both that copyright notice and this permission notice appear in 
supporting documentation, and that the names of Stichting Mathematisch
Centrum or CWI not be used in advertising or publicity pertaining to
distribution of the software without specific, written prior permission.

STICHTING MATHEMATISCH CENTRUM DISCLAIMS ALL WARRANTIES WITH REGARD TO
THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS, IN NO EVENT SHALL STICHTING MATHEMATISCH CENTRUM BE LIABLE
FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT
OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

******************************************************************/

/*
** Resource-IDs in use by Python.
**
** All resources used by the python interpreter itself fall
** in the range 228-256. The range 128-228 is not used, because
** there is too much chance of conflicts with other packages.
**
** Standard python modules use resources in the range
** 256-512.
**
** Python programs that use their own resources are advised to
** choose resource numbers higher than 512.
*/

/*
** Resources that reside in the python executable (or, for
** shared ppc python, in the core dynamic library)
*/

/* The alert for "No Python directory, where is it?" (OBSOLETE) */
#define NOPYTHON_ALERT	228
#define YES_ITEM		1
#define NO_ITEM			2
#define CURWD_ITEM		3

/* The alert for "this is an applet template" */
#define NOPYC_ALERT		229

/* The dialog for our GetDirectory and PromptGetFile call */
#define GETDIR_ID 		230		/* Resource ID for our "get directory" */
#define GETFILEPROMPT_ID 232	/* Resource id for prompted get file */
#define PROMPT_ITEM		10		/* The prompt, at the top */
#define SELECTCUR_ITEM	11	/* "Select current directory" button */


/* The dialog for interactive options */
#define OPT_DIALOG		231		/* Resource ID for dialog */
#define OPT_OK			1
#define OPT_CANCEL		2
#define OPT_INSPECT		3
#define OPT_VERBOSE		4
#define OPT_OPTIMIZE	5
#define OPT_UNBUFFERED	6
#define OPT_DEBUGGING	7
#define OPT_KEEPNORMAL	8
#define OPT_KEEPERROR	9
#define OPT_CMDLINE		10
#define OPT_OLDEXC	13
#define OPT_NOSITE	14
#define OPT_HELP	16

/* Dialog for 'No preferences directory' */
#define NOPREFDIR_ID	233

/* Dialog for 'Bad or outdated preferences' */
#define BADPREFERENCES_ID	234
#define BADPREF_DELETE		1
#define BADPREF_CONTINUE	2
#define BADPREF_QUIT		3
/* Dialog for 'Bad preference file' */
#define BADPREFFILE_ID	235

/* About box */
#define ABOUT_ID		236

/* No preferences file name resource */
#define NOPREFNAME_ID	237

/* EditPythonPrefs range. Needed here to forestall conflicts with applets */
#define EDITPYTHONPREFS_MIN	508
#define EDITPYTHONPREFS_MAX 511
/* twit range. Again needed to forestall conflicts with scripts using their own resources */
#define TWIT_MIN		500
#define TWIT_MAX		507
/* Bruce range. The same */
#define BRUCE_MIN		468
#define BRUCE_MAX		499

/*
** The following are valid both in the binary (or shared library)
** and in the Preferences file.
** For all these the override is tried first, in the application resource fork
** only, this allows an applet to override standard settings.
** If there is no override resource the preferences file is added to the head
** of the resource file chain and the non-override version of the resource is
** searched in any resource file.
**
** The effect of this is that, for example, a 'Popt' of 228 in the application or
** shared library provides default options for use when no preferences are set,
** while a 'Popt' of 229 (in the application *only*) overrides any options in the
** preferences file.
*/

/* The STR resource that holds the preference file name */
#define PREFFILENAME_ID 228		/* For Rez only */
#define PREFFILENAME_PASCAL_NAME "PythonPreferenceFileName"
#define PREFFILENAME_NAME "\pPythonPreferenceFileName"

/* The STR# resource for sys.path initialization */
#define PYTHONPATH_ID 228
#define PYTHONPATHOVERRIDE_ID 229

/* The alis resource for locating the python home directory */
#define PYTHONHOME_ID 228
#define PYTHONHOMEOVERRIDE_ID 229

/* The Python options resource and offset of its members */
#define PYTHONOPTIONS_ID 228
#define PYTHONOPTIONSOVERRIDE_ID 229
#if 0
#define POPT_INSPECT	0
#define POPT_VERBOSE	1
#define POPT_OPTIMIZE	2
#define POPT_UNBUFFERED	3
#define POPT_DEBUGGING	4
#define POPT_KEEPNORM	5
#define POPT_KEEPERR	6
#endif

#define POPT_VERSION_CURRENT	4	/* Current version number */

#ifndef rez
typedef struct PyMac_PrefRecord {
	unsigned char	version;
	unsigned char	inspect;
	unsigned char	verbose;
	unsigned char	optimize;
	unsigned char	unbuffered;
	unsigned char	debugging;
	unsigned char	keep_normal;
	unsigned char	keep_error;
	unsigned char	nointopt;
	unsigned char	noargs;
	unsigned char	oldexc;
	unsigned char	nosite;
} PyMac_PrefRecord;
#endif

/* The GUSI options resources */
#define GUSIOPTIONS_ID	10240
#define GUSIOPTIONSOVERRIDE_ID 10241

#ifndef rez
/* From macgetpath.c: */
void PyMac_PreferenceOptions Py_PROTO((PyMac_PrefRecord *));
char * PyMac_GetPythonDir Py_PROTO((void));
#endif