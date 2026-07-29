
RJ2XCLModule
==========

Support functions for [RJ2XCL][1].

Overview
--------

This module is part of RJ2XCL, and probably not useful on its own.

Some RJ2XCL functionality (primarily R, but some C++ as well) is 
moving out of the core and into a separate module.  This is 
happening for two reasons: (1) proper namespacing; (2) proper 
documentation for functions; and (3) the graphics device.  

Regarding the last one, building the module allows better interfacing
with R as RJ2XCL is built using MSVC while R on Windows is (usually) 
built with [mingw][3].

License 
-------

[GPL v2][2].  Copyright (c) 2017 Structured Data, LLC.

Build and install
-----------------

Set appropriate environment variables (see generally docs on
building modules; you will need Windows R build tools installed). 
To generate package and documentation files,

```
> R -e "library(roxygen2); roxygenise('RJ2XCLModule');"
```

Build with

```
> R CMD build RJ2XCLModule && R CMD INSTALL RJ2XCLModule
```

[1]: https://RJ2XCL-toolkit.com
[2]: https://opensource.org/licenses/gpl-2.0.php
[3]: http://www.mingw.org/

