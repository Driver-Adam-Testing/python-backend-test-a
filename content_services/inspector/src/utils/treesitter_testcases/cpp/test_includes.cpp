// Standard library includes
#include <iostream>
#include <vector>
#include <string>
#include <memory>
#include <algorithm>
#include <map>
#include <unordered_map>
#include <thread>
#include <future>

// System includes with spaces and variations
#include    <cstdio>
#  include <cstdlib>

// Local includes
#include "myheader.h"
#include "../headers/another_header.hpp"
#include "utils/utility.h"
#include "core/engine.hpp"

// Conditional includes
#ifdef USE_OPENGL
    #include <GL/gl.h>
    #include <GL/glu.h>
#endif

#if defined(WIN32) || defined(_WIN32)
    #include <windows.h>
#elif defined(__linux__)
    #include <unistd.h>
#else
    #include <sys/types.h>
#endif

// Boost or other third-party includes
#include <boost/algorithm/string.hpp>
#include <fmt/format.h>

int main() {
    return 0;
}
