//go:build !windows

package mobile

import (
	"os"
	"syscall"
)

// dupFile wraps a duplicate of fd, so closing it leaves the caller's open.
// The descriptor comes from Java (ParcelFileDescriptor.detachFd), so this is
// the Android path; the Windows variant only exists so the package builds for
// development and testing on a Windows host.
func dupFile(fd int, name string) (*os.File, error) {
	dup, e := syscall.Dup(fd)
	if e != nil {
		return nil, e
	}
	return os.NewFile(uintptr(dup), name), nil
}
