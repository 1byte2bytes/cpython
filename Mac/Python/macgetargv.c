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

/* Construct argc and argv for main() by using Apple Events */
/* From Jack's implementation for STDWIN */

#include <stdlib.h>

#ifndef SystemSevenOrLater
#define SystemSevenOrLater 1
#endif

#include <Types.h>
#include <Files.h>
#include <Events.h>
#include <Memory.h>
#include <Processes.h>
#include <Errors.h>
#include <AppleEvents.h>
#include <AEObjects.h>
#include <Fonts.h>
#include <TextEdit.h>
#include <Menus.h>
#include <Dialogs.h>
#include <Windows.h>

#include "Python.h"
#include "macglue.h"

#ifdef GENERATINGCFM	/* Defined to 0 or 1 in Universal headers */
#define HAVE_UNIVERSAL_HEADERS
#endif

#ifdef SYMANTEC__CFM68K__
#pragma lib_export on
#endif

#ifndef HAVE_UNIVERSAL_HEADERS
#define NewAEEventHandlerProc(x) (x)
#define AEEventHandlerUPP EventHandlerProcPtr
#endif

static int arg_count;
static char *arg_vector[256];
FSSpec PyMac_ApplicationFSSpec;
char PyMac_ApplicationPath[256];
static int applocation_inited;

/* Duplicate a string to the heap. We also export this since it isn't standard
** and others use it
*/

char *
strdup(char *src)
{
	char *dst = malloc(strlen(src) + 1);
	if (dst)
		strcpy(dst, src);
	return dst;
}

/* Initialize FSSpec and full name of current application */

OSErr
PyMac_init_process_location()
{
	ProcessSerialNumber currentPSN;
	ProcessInfoRec info;
	OSErr err;
	
	if ( applocation_inited ) return 0;
	currentPSN.highLongOfPSN = 0;
	currentPSN.lowLongOfPSN = kCurrentProcess;
	info.processInfoLength = sizeof(ProcessInfoRec);
	info.processName = NULL;
	info.processAppSpec = &PyMac_ApplicationFSSpec;
	if ( err=GetProcessInformation(&currentPSN, &info))
		return err;
	if ( err=PyMac_GetFullPath(&PyMac_ApplicationFSSpec, PyMac_ApplicationPath) )
		return err;
	applocation_inited = 1;
	return 0;
}

/* Given an FSSpec, return the FSSpec of the parent folder */

static OSErr
get_folder_parent (FSSpec * fss, FSSpec * parent)
{
	CInfoPBRec rec;
	short err;

        * parent = * fss;
        rec.hFileInfo.ioNamePtr = parent->name;
        rec.hFileInfo.ioVRefNum = parent->vRefNum;
        rec.hFileInfo.ioDirID = parent->parID;
		rec.hFileInfo.ioFDirIndex = -1;
        rec.hFileInfo.ioFVersNum = 0;
        if (err = PBGetCatInfoSync (& rec))
        	return err;
        parent->parID = rec.dirInfo.ioDrParID;
/*	parent->name[0] = 0; */
        return 0;
}

/* Given an FSSpec return a full, colon-separated pathname */

OSErr
PyMac_GetFullPath (FSSpec *fss, char *buf)
{
	short err;
	FSSpec fss_parent, fss_current;
	char tmpbuf[256];
	int plen;

	fss_current = *fss;
	plen = fss_current.name[0];
	memcpy(buf, &fss_current.name[1], plen);
	buf[plen] = 0;
	/* Special case for disk names */
	if ( fss_current.parID <= 1 ) {
		buf[plen++] = ':';
		buf[plen] = 0;
		return 0;
	}
	while (fss_current.parID > 1) {
    		/* Get parent folder name */
                if (err = get_folder_parent(&fss_current, &fss_parent))
             		return err;
                fss_current = fss_parent;
                /* Prepend path component just found to buf */
    			plen = fss_current.name[0];
    			if (strlen(buf) + plen + 1 > 256) {
    				/* Oops... Not enough space (shouldn't happen) */
    				*buf = 0;
    				return -1;
    			}
    			memcpy(tmpbuf, &fss_current.name[1], plen);
    			tmpbuf[plen] = ':';
    			strcpy(&tmpbuf[plen+1], buf);
    			strcpy(buf, tmpbuf);
        }
        return 0;
}

/* Check that there aren't any args remaining in the event */

static OSErr 
get_missing_params(AppleEvent *theAppleEvent)
{
	DescType theType;
	Size actualSize;
	OSErr err;
	
	err = AEGetAttributePtr(theAppleEvent, keyMissedKeywordAttr, typeWildCard,
				&theType, nil, 0, &actualSize);
	if (err == errAEDescNotFound)
		return noErr;
	else
		return errAEEventNotHandled;
}

static int got_one; /* Flag that we can stop getting events */

/* Handle the Print or Quit events (by failing) */

static pascal OSErr
handle_not(AppleEvent *theAppleEvent, AppleEvent *reply, long refCon)
{
	#pragma unused (reply, refCon)
	got_one = 1;
	return errAEEventNotHandled;
}

/* Handle the Open Application event (by ignoring it) */

static pascal OSErr
handle_open_app(AppleEvent *theAppleEvent, AppleEvent *reply, long refCon)
{
	#pragma unused (reply, refCon)
#if 0
	/* Test by Jack: would removing this facilitate debugging? */
	got_one = 1;
#endif
	return get_missing_params(theAppleEvent);
}

/* Handle the Open Document event, by adding an argument */

static pascal OSErr
handle_open_doc(AppleEvent *theAppleEvent, AppleEvent *reply, long refCon)
{
	#pragma unused (reply, refCon)
	OSErr err;
	AEDescList doclist;
	AEKeyword keywd;
	DescType rttype;
	long i, ndocs, size;
	FSSpec fss;
	char path[256];
	
	got_one = 1;
	if (err = AEGetParamDesc(theAppleEvent,
				 keyDirectObject, typeAEList, &doclist))
		return err;
	if (err = get_missing_params(theAppleEvent))
		return err;
	if (err = AECountItems(&doclist, &ndocs))
		return err;
	for(i = 1; i <= ndocs; i++) {
		err = AEGetNthPtr(&doclist, i, typeFSS,
				  &keywd, &rttype, &fss, sizeof(fss), &size);
		if (err)
			break;
		PyMac_GetFullPath(&fss, path);
		arg_vector[arg_count++] = strdup(path);
	}
	return err;
}

/* Install standard core event handlers */
AEEventHandlerUPP open_doc_upp;
AEEventHandlerUPP open_app_upp;
AEEventHandlerUPP not_upp;

static void
set_ae_handlers()
{
	open_doc_upp = NewAEEventHandlerProc(handle_open_doc);
	open_app_upp = NewAEEventHandlerProc(handle_open_app);
	not_upp = NewAEEventHandlerProc(handle_not);
	
	AEInstallEventHandler(kCoreEventClass, kAEOpenApplication,
			      open_app_upp, 0L, false);
	AEInstallEventHandler(kCoreEventClass, kAEOpenDocuments,
			      open_doc_upp, 0L, false);
	AEInstallEventHandler(kCoreEventClass, kAEPrintDocuments,
			      not_upp, 0L, false);
	AEInstallEventHandler(kCoreEventClass, kAEQuitApplication,
			      not_upp, 0L, false);
}

/* Uninstall standard core event handlers */

static void
reset_ae_handlers()
{
	AERemoveEventHandler(kCoreEventClass, kAEOpenApplication,
			     open_app_upp, false);
	AERemoveEventHandler(kCoreEventClass, kAEOpenDocuments,
			     open_doc_upp, false);
	AERemoveEventHandler(kCoreEventClass, kAEPrintDocuments,
			     not_upp, false);
	AERemoveEventHandler(kCoreEventClass, kAEQuitApplication,
			     not_upp, false);
}

/* Wait for events until a core event has been handled */

static void 
event_loop()
{
	EventRecord event;
	int n;
	int ok;
	
	got_one = 0;
	for (n = 0; n < 100 && !got_one; n++) {
		SystemTask();
		ok = GetNextEvent(everyEvent, &event);
		if (ok && event.what == kHighLevelEvent) {
			AEProcessAppleEvent(&event);
		}
	}
}

/* Get the argv vector, return argc */

int
PyMac_GetArgv(pargv, noevents)
	char ***pargv;
	int noevents;
{
	
	arg_count = 0;
	(void)PyMac_init_process_location();
	arg_vector[arg_count++] = strdup(PyMac_ApplicationPath);
	
	if( !noevents ) {
		set_ae_handlers();
		event_loop();
		reset_ae_handlers();
	}
	
	arg_vector[arg_count] = NULL;
	
	*pargv = arg_vector;
	return arg_count;
}
