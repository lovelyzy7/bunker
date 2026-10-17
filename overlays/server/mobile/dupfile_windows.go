//go:build windows

package mobile

import (
	"os"
	"syscall"
)

// dupFile duplicates the descriptor so that closing the copy leaves the
// caller's file open, as the Unix syscall.Dup version does. Go reports the
// Windows duplicate as a HANDLE, which os.NewFile accepts.
func dupFile(fd int, name string) (*os.File, error) {
	self, e := syscall.GetCurrentProcess()
	if e != nil {
		return nil, e
	}
	var dup syscall.Handle
	if e = syscall.DuplicateHandle(self, syscall.Handle(fd), self, &dup, 0, false, syscall.DUPLICATE_SAME_ACCESS); e != nil {
		return nil, e
	}
	return os.NewFile(uintptr(dup), name), nil
}
