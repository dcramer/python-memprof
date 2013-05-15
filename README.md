python-memprof
==============

**Barely works**

The idea is to capture a memory snapshot (of Python objects) when a threshold
is hit.

Once you've captured some, you should be able to semi-easily identify which
objects are using the most memory based on count + total size and have some
kind of identifying information which might point you to what was creating
these objects.

Usage
-----

Collect data:

	memprof -t 100mb my_python_script.py


Analyze data:

(TODO: move this to memprof-analyze)

	python memprof/profiler.py output.json
