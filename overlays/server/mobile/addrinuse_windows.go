//go:build windows

package mobile

import "syscall"

// errAddrInUse is the error net.Listen wraps when the port is taken. Windows
// reports the Winsock code (WSAEADDRINUSE, 10048), not the Unix errno that Go
// names EADDRINUSE, and syscall does not export the Winsock name.
var errAddrInUse error = syscall.Errno(10048)
