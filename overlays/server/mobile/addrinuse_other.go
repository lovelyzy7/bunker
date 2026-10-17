//go:build !windows

package mobile

import "syscall"

// errAddrInUse is the error net.Listen wraps when the port is taken.
var errAddrInUse = syscall.EADDRINUSE
