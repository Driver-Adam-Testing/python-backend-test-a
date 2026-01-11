// Test cases for Go import statements
package main

// 1) Single import
import "fmt"

// 2) Multiple imports (grouped)
import (
	"context"
	"encoding/json"
)

// 3) Import with alias
import (
	stdlog "log"
	stdjson "encoding/json"
)

// 4) Import with dot notation (import into current namespace)
import (
	. "fmt"
	. "math"
)

// 5) Import with blank identifier (side effects only)
import (
	_ "database/sql/driver"
	_ "image/png"
)

// 6) Third-party imports (examples of common patterns)
import (
	// Database drivers
	_ "github.com/lib/pq"           // PostgreSQL
	_ "github.com/go-sql-driver/mysql" // MySQL
	_ "github.com/mattn/go-sqlite3"    // SQLite

	// Web frameworks
	"github.com/gin-gonic/gin"
	"github.com/gorilla/mux"
	"github.com/labstack/echo/v4"
)

// 7) Internal package imports (relative to module)
import (
	"myproject/internal/config"
	"myproject/internal/database"
)

// 8) Renamed imports to avoid conflicts
import (
	cryptorand "crypto/rand"
	mathrand "math/rand"
)

// 9) Build constraints examples (as comments)
/*
//go:build !windows
package main

import "golang.org/x/sys/unix"

//go:build windows
package main

import "golang.org/x/sys/windows"

//go:build linux && amd64
package main

import "runtime"

//go:build cgo
package main

import "C"
*/
