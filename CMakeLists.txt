cmake_minimum_required(VERSION 2.8.9)
project(Python)
include_directories(Include/)

add_library(Parser Parser/acceler.c Parser/bitset.c Parser/firstsets.c Parser/grammar.c Parser/grammar1.c Parser/intrcheck.c 
Parser/listnode.c Parser/metagrammar.c Parser/myreadline.c Parser/node.c Parser/parser.c Parser/parsetok.c Parser/pgen.c
Parser/printgrammar.c Parser/tokenizer.c)

add_library(Objects Objects/abstract.c Objects/bufferobject.c Objects/classobject.c Objects/cobject.c Objects/complexobject.c 
Objects/dictobject.c Objects/floatobject.c Objects/fileobject.c Objects/frameobject.c Objects/funcobject.c Objects/intobject.c
Objects/listobject.c Objects/longobject.c Objects/methodobject.c Objects/moduleobject.c Objects/object.c Objects/rangeobject.c 
Objects/sliceobject.c Objects/stringobject.c Objects/tupleobject.c Objects/typeobject.c)

add_library(Modules Modules/getpath.c Modules/getbuildinfo.c Modules/config.c)

add_executable(Python Python/atof.c Python/bltinmodule.c Python/ceval.c Python/compile.c Python/dup2.c Python/errors.c Python/fmod.c
Python/frozen.c Python/frozenmain.c Python/getargs.c Python/getcompiler.c Python/getcopyright.c Python/getcwd.c Python/getmtime.c
Python/getopt.c Python/getplatform.c Python/getversion.c Python/graminit.c Python/hypot.c Python/import.c Python/importdl.c
Python/marshal.c Python/modsupport.c Python/mystrtoul.c Python/pyfpe.c Python/pystate.c Python/sigcheck.c
Python/strdup.c Python/strerror.c Python/strtod.c Python/structmember.c Python/sysmodule.c Python/thread.c Python/traceback.c
Python/pythonmain.c Python/pythonrun.c)

target_link_libraries(Python Parser)
target_link_libraries(Python Objects)
target_link_libraries(Python Modules)