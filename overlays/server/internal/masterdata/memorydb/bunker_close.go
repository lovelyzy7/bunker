package memorydb

// Close releases the open master-data file. Windows keeps an open file locked
// against deletion, so a master copied into a temporary directory stays there
// until this is called (the tests' cleanup); Android replaces the asset folder
// after the server has stopped. Call only with no ReadTable in flight.
func Close() {
	if tables != nil && tables.file != nil {
		tables.file.Close()
	}
}
