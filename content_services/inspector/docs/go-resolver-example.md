# Go Resolver Implementation Example

This document explains how our GoResolver works with a concrete example of a multi-module repository.

## Path Structure

**Important:** All file paths in our system are **relative to the repository root** with the repository name as the first component:

```python
# Input paths are always in this format:
Path("company-monorepo/backend/main.go")
Path("company-monorepo/backend/api/handlers.go")
Path("company-monorepo/shared/types/user.go")
```

## Example Repository Structure

```
company-monorepo/
├── backend/
│   ├── go.mod                    # module "github.com/company/backend"
│   ├── main.go
│   ├── api/
│   │   ├── handlers.go
│   │   └── middleware.go
│   └── db/
│       └── connection.go
├── shared/
│   ├── go.mod                    # module "github.com/company/shared"
│   ├── types/
│   │   └── user.go
│   └── utils/
│       └── validator.go
└── tools/
    ├── go.mod                    # module "github.com/company/tools"
    └── migrate/
        └── main.go
```

## Step-by-Step Processing

### Step 1: File Grouping

Our resolver groups files by their nearest `go.mod`:

```python
module_groups = {
    Path("company-monorepo/backend/go.mod"): {
        Path("company-monorepo/backend/main.go"),
        Path("company-monorepo/backend/api/handlers.go"),
        Path("company-monorepo/backend/api/middleware.go"),
        Path("company-monorepo/backend/db/connection.go")
    },
    Path("company-monorepo/shared/go.mod"): {
        Path("company-monorepo/shared/types/user.go"),
        Path("company-monorepo/shared/utils/validator.go")
    },
    Path("company-monorepo/tools/go.mod"): {
        Path("company-monorepo/tools/migrate/main.go")
    }
}
```

### Step 2: Package Mappings Per Module

**Backend Module:**
```python
# Module root: Path("company-monorepo/backend")
package_mapping = {
    "github.com/company/backend": [
        Path("company-monorepo/backend/main.go")
    ],
    "github.com/company/backend/api": [
        Path("company-monorepo/backend/api/handlers.go"),
        Path("company-monorepo/backend/api/middleware.go")
    ],
    "github.com/company/backend/db": [
        Path("company-monorepo/backend/db/connection.go")
    ]
}
```

**Shared Module:**
```python
# Module root: Path("company-monorepo/shared")
package_mapping = {
    "github.com/company/shared/types": [
        Path("company-monorepo/shared/types/user.go")
    ],
    "github.com/company/shared/utils": [
        Path("company-monorepo/shared/utils/validator.go")
    ]
}
```

**Tools Module:**
```python
# Module root: Path("company-monorepo/tools")
package_mapping = {
    "github.com/company/tools/migrate": [
        Path("company-monorepo/tools/migrate/main.go")
    ]
}
```

### Step 3: Import Resolution Examples

#### File: `company-monorepo/backend/main.go`
```go
package main

import (
    "fmt"                                    // Standard library - IGNORED
    "github.com/gin-gonic/gin"              // External dependency - IGNORED
    "github.com/company/backend/api"        // Local import - RESOLVED
    "github.com/company/backend/db"         // Local import - RESOLVED
    "github.com/company/shared/types"       // Different module - IGNORED
)
```

**Resolution Results:**
- `"fmt"` → No resolution (standard library)
- `"github.com/gin-gonic/gin"` → No resolution (external dependency)
- `"github.com/company/backend/api"` → **Resolves to:** `[handlers.go, middleware.go]`
- `"github.com/company/backend/db"` → **Resolves to:** `[connection.go]`
- `"github.com/company/shared/types"` → No resolution (different module)

#### File: `company-monorepo/shared/types/user.go`
```go
package types

import (
    "github.com/company/shared/utils"       // Local import - RESOLVED
    "github.com/company/backend/api"        // Different module - IGNORED
)
```

**Resolution Results:**
- `"github.com/company/shared/utils"` → **Resolves to:** `[validator.go]`
- `"github.com/company/backend/api"` → No resolution (different module)

#### File: `company-monorepo/tools/migrate/main.go`
```go
package main

import (
    "database/sql"                          // Standard library - IGNORED
    "github.com/company/backend/db"         // Different module - IGNORED
    "github.com/company/shared/types"       // Different module - IGNORED
)
```

**Resolution Results:**
- `"database/sql"` → No resolution (standard library)
- `"github.com/company/backend/db"` → No resolution (different module)
- `"github.com/company/shared/types"` → No resolution (different module)

## Key Behaviors

✅ **Module Isolation**: Backend can't import from shared, tools can't import from backend
✅ **Local Resolution**: Only imports matching the module name resolve to project files
✅ **External Filtering**: Standard library and dependencies are ignored
✅ **Efficient Lookup**: O(1) dictionary lookup instead of scanning all files
✅ **Monorepo Support**: Handles multiple modules in the same repository correctly

## Path Operations Example

Here's how the path operations work with our repo-relative structure:

```python
# For file: Path("company-monorepo/backend/api/handlers.go")
# Module root: Path("company-monorepo/backend")

file_path.parent = Path("company-monorepo/backend/api")
module_root = Path("company-monorepo/backend")

# Calculate relative path within module
rel_path = file_path.parent.relative_to(module_root)
# = Path("api")

# Build package path (Go imports always use forward slashes)
package_path = f"{module_name}/{rel_path.as_posix()}"
# = "github.com/company/backend/api"
```

## Algorithm Summary

1. **Group files by nearest go.mod** - Handles monorepos with multiple modules
2. **Extract module name** - From each go.mod file
3. **Build package mappings** - Map import paths to actual files within each module using repo-relative paths
4. **Process imports per module** - Only resolve imports within the same module context
5. **Fast dictionary lookup** - O(1) resolution instead of O(n) file scanning

This correctly models Go's module system where each module is self-contained and can only reference its own internal packages. All path operations work with repo-relative paths that include the repository name as the first component.
