"""A library for selectively tracing/timing execution.

Traditional profiling in Python is performed by hooking into the function
call machinery so that every call is timed; occasionally, a tool will
allow certain functions or modules to be ignored. The forest is often
lost for the trees. Silhouette operates selectively instead, allowing
you to focus on the important concepts in your domain. You can:

 * Add function decorators or context managers to your code to get a
   context-rich call graph, complete with timings.
 * Annotate any call node with arbitrary metadata, to help explain
   why you received the results you did.
 * Print calls as they execute and/or collect them for later analysis.
 * Return silhouette call graphs from other services and integrate
   them into your local graph. Distributed tracing ftw!

Due to overhead, silhouette is disabled by default.
To enable, the environment variable SILHOUETTE_ENABLE must be set.

See the script 'trace2dot.py' in the tools repo for a post-processor
which creates a graphical representation.
"""

from . import tagging, tracing
