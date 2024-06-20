# Folder Synchronization

This program synchronizes the contents of a source folder with a replica folder.
Regular files and directories are synchronized.
The synchronization is one-way, from the source to the replica, and is performed periodically
based on a specified interval.

## Usage

Run the program with the following command-line arguments:

```sh
python sync_folders.py <source_folder> <replica_folder> <sync_interval> <log_file>
```

- `<source_folder>`: Path to the source folder
- `<replica_folder>`: Path to the replica folder
- `<sync_interval>`: Synchronization interval in seconds (must be a positive number)
- `<log_file>`: Path to the log file

### Example

```sh
python sync_folders.py '/path/to/source' '/path/to/replica' 120 '/path/to/logfile.log'
```

### Stop Signal

The program can be stopped by placing a specific file named stop_synch.txt in the source folder.
Upon detecting this file, the program will stop synchronization and exit gracefully.

## Author

Katerina Simkova

## Date

June 20, 2024
