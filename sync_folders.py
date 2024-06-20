"""
Folder Synchronization

This program synchronizes the contents of a source folder with a replica folder. 
Regular files and directories are synchronized.
The synchronization is one-way, from the source to the replica, and is performed periodically 
based on a specified interval.

Features:
- One-way synchronization from the source folder to the replica folder
- Periodic synchronization at a user-defined interval
- Detailed logging of file operations to both the console and a log file
- Synchronization is stopped when stop signal file is detected


Usage:
Run the program with the following command-line arguments:

    python sync_folders.py <source_folder> <replica_folder> <sync_interval> <log_file>

Arguments:
- <source_folder>: Absolute path to the source folder
- <replica_folder>: Absolute path to the replica folder
- <sync_interval>: Synchronization interval in seconds (must be a positive number)
- <log_file>: Absolute path to the log file

Example:
    python sync_folders.py '/path/to/source' '/path/to/replica' 120 '/path/to/logfile.log'

Stop Signal
The program can be stopped by placing a file named stop_sync.txt in the source folder.
Upon detecting this file, the program will stop synchronization and exit gracefully.


Author: Katerina Simkova
Date: June 20, 2024

"""

import argparse
import filecmp
import logging
import os
import shutil
import sys
import time


def configure_logging(log_file_path):
    """
    Sets up logging for the program. Logs to stdout and to a file if logging is enabled.
    :param log_file_path: Absolute path of the log file.
    :return: Logger object.
    """
    logger = logging.getLogger(__name__)

    logger.setLevel(logging.INFO)

    s_handler = logging.StreamHandler(sys.stdout)
    f_handler = logging.FileHandler(log_file_path)

    s_formatter = logging.Formatter('%(asctime)s::%(name)s::%(levelname)s::%(message)s')
    f_formatter = logging.Formatter('%(asctime)s::%(name)s::%(levelname)s::%(message)s')
    s_handler.setFormatter(s_formatter)
    f_handler.setFormatter(f_formatter)

    logger.addHandler(s_handler)
    logger.addHandler(f_handler)
    return logger


def valid_dir(path):
    """
    Checks if a path is a valid directory.
    """
    if not os.path.isdir(path):
        raise argparse.ArgumentTypeError("Directory {} does not exist.".format(path))
    return path


def valid_file(path):
    """
    Checks if a path is a valid file.
    """
    if not os.path.isfile(path):
        raise argparse.ArgumentTypeError("File {}: does not exist.".format(path))
    return path


def valid_interval(interval):
    """
    Checks if a synchronization interval is valid number.
    :return: Float number.
    """

    try:
        interval = float(interval)
        if interval <= 0:
            raise argparse.ArgumentTypeError("Synchronization interval must be a positive number.")
        return interval
    except ValueError:
        raise argparse.ArgumentTypeError("Synchronization interval must be a number.")


def is_folder_empty(path):
    """
    Checks if a directory is empty.
    :param path: Absolute path to a directory.
    :return: True if directory is empty, else False.
    """
    return not os.listdir(path)


def copy_file(source_path, replica_path, logger):
    """Copies files from source to replica.
    :param source_path: Absolute path of file in source folder.
    :param replica_path: Absolute path of file in replica folder.
    :param logger: Logger object.
    """
    try:
        shutil.copy2(source_path, replica_path)
        logger.info("File {} copied to replica.".format(source_path))
    except FileNotFoundError:
        logger.exception("File {} not found. File cannot be copied.".format(source_path))
    except PermissionError:
        logger.exception("Permission denied for file {}. File cannot be copied.".format(source_path))
    except shutil.SpecialFileError:
        logger.exception("Unsupported file type for file {}. File cannot be copied".format(source_path))
    except shutil.Error:
        logger.exception("Error while copying file {}. File cannot be copied.".format(source_path))
    except OSError:
        logger.exception("Error while copying file {}. File cannot be copied.".format(source_path))


def copy_directory(source_path, replica_path, logger):
    """Copies directory and its files and subdirectories from source to replica.
    :param source_path: Absolute path of file or directory in source folder.
    :param replica_path: Absolute path of file or directory in replica folder.
    :param logger: Logger object.
    """
    try:
        shutil.copytree(source_path, replica_path)
        logger.info("Directory {} and its contents copied to replica.".format(source_path))
    except FileNotFoundError:
        logger.exception("Directory {} not found. Directory cannot be copied.".format(source_path))
    except PermissionError:
        logger.exception("Permission denied for directory {}. Directory cannot be copied.".format(source_path))
    except shutil.Error:
        logger.exception("Error while copying directory {}. Directory cannot be copied.".format(source_path))
    except OSError:
        logger.exception("Error while copying directory {}. Directory cannot be copied.".format(source_path))


def copy_to_replica(source_path, replica_path, logger):
    """Copy all new or modified files from source folder to replica folder.
    If file does not exist in replica, it will be created in replica.
    If file exists in replica and has been modified in source folder, it will be overwritten in replica.
    If directory does not exist in replica, it will be created and all its contents will be copied.
    If directory exists in replica but its contents in source folder have been changed,
    new subdirectories will be created and modified files will be overwritten.
    :param source_path: Absolute path of source folder.
    :param replica_path: Absolute path of replica folder.
    :param logger: Logger object.
    """
    source_all_files = os.listdir(source_path)
    replica_all_files = os.listdir(replica_path)
    for file in source_all_files:
        file_path_src = os.path.join(source_path, file)
        file_path_rpl = os.path.join(replica_path, file)

        if not os.path.exists(file_path_rpl):
            if os.path.isfile(file_path_src):
                copy_file(file_path_src, file_path_rpl, logger)

            elif os.path.isdir(file_path_src):
                copy_directory(file_path_src, file_path_rpl, logger)

        elif os.path.isfile(file_path_src):
            if os.path.isfile(file_path_rpl):
                if not is_same_file(file_path_src, file_path_rpl):
                    # if versions of file in source and replica are different, overwrites file in replica
                    copy_file(file_path_src, file_path_rpl, logger)
            elif os.path.isdir(file_path_rpl):
                # if same path leads to file in source and directory in replica, overwrite directory in replica
                remove_directory(file_path_rpl, logger)
                copy_file(file_path_src, file_path_rpl, logger)

        elif os.path.isdir(file_path_src):
            if os.path.isdir(file_path_rpl):
                # if directory exists in source, compares its contents to source
                copy_to_replica(file_path_src, file_path_rpl, logger)
            elif os.path.isfile(file_path_rpl):
                # if same path leads to directory in source and file in replica, overwrite file in replica
                remove_file(file_path_rpl, logger)
                copy_directory(file_path_src, file_path_rpl, logger)


def remove_file(path, logger):
    """Removes file.
    :param path: Absolute path of file to be removed.
    :param logger: Logger object.
    """
    try:
        os.remove(path)
        logger.info("File {} removed from replica".format(path))
    except FileNotFoundError:
        logger.exception("File {} not found. File cannot be removed.".format(path))
    except PermissionError:
        logger.exception("Permission denied for file {}. File cannot be removed.".format(path))
    except OSError:
        logger.exception("Error while removing file {}.".format(path))


def remove_directory(path, logger):
    """Removes directory and its contents.
    :param path: Absolute path of directory to be removed.
    :param logger: Logger object.
    """
    try:
        shutil.rmtree(path)
        logger.info("Directory {} and its contents removed from replica".format(path))
    except FileNotFoundError:
        logger.exception("Directory {} not found. Directory cannot be removed.".format(path))
    except PermissionError:
        logger.exception("Permission denied for directory {}. Directory cannot be removed.".format(path))
    except shutil.Error:
        logger.exception("Error while removing directory {}. Directory cannot be removed.".format(path))
    except OSError:
        logger.exception("Error while removing directory {}.".format(path))


def remove_from_replica(source_path, replica_path, logger):
    """Removes files and directories from replica.
    If file does not exist in source, it will be removed.
    If directory does not exist in source, it will be removed with all its files and subdirectories.
    :param source_path: Absolute path of source folders.
    :param replica_path: Absolute path of replica folder.
    :param logger: Logger object.
    """
    replica_all_files = os.listdir(replica_path)
    for file in replica_all_files:
        file_path_src = os.path.join(source_path, file)
        file_path_rpl = os.path.join(replica_path, file)

        if not os.path.exists(file_path_src) and os.path.isfile(file_path_rpl):
            remove_file(file_path_rpl, logger)

        elif not os.path.exists(file_path_src) and os.path.isdir(file_path_rpl):
            remove_directory(file_path_rpl, logger)

        elif os.path.exists(file_path_src) and os.path.isdir(file_path_rpl):
            # if directory exists in source, check its contents
            # remove those files and subdirectories that do not exist in its source counterpart
            remove_from_replica(file_path_src, file_path_rpl, logger)

        # note: if file exists in both source and replica, it was synchronized in previous steps
    return


def is_same_file(file_path_src, file_path_rpl):
    """Compares two files.
    :param file_path_src: Absolute path of source file.
    :param file_path_rpl: Absolute path of replica file.
    :return bool: True if the two files are equal, False otherwise.
    """
    filecmp.clear_cache()
    return filecmp.cmp(file_path_src, file_path_rpl, shallow=False)


def synch_folders(source_path, replica_path, logger):
    """
    Synchronizes files and directories from source folder to replica folder.
    New files and directories from source folder are copied to replica folder.
    Files and directories modified in the source folder are copied to replica folder.
    Files and directories deleted from source folder are removed from replica folder.
    :param source_path: Absolute path of source folder.
    :param replica_path: Absolute path of replica folder.
    :param logger: Logger object.
    """
    if is_folder_empty(source_path) and is_folder_empty(replica_path):
        return

    if is_folder_empty(source_path) and not is_folder_empty(replica_path):
        remove_from_replica(source_path, replica_path, logger)
        return

    if not is_folder_empty(source_path) and is_folder_empty(replica_path):
        copy_to_replica(source_path, replica_path, logger)
        return

    copy_to_replica(source_path, replica_path, logger)
    remove_from_replica(source_path, replica_path, logger)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source_path", type=valid_dir, help="Source folder path (absolute path)")
    parser.add_argument("replica_path", type=valid_dir, help="Replica folder path (absolute path)")
    parser.add_argument("synch_interval", type=valid_interval, help="Synch interval in seconds (positive number)")
    parser.add_argument("log_path", type=valid_file, help="Log file path (absolute path)")

    args = parser.parse_args()

    source_path = args.source_path
    replica_path = args.replica_path
    synch_interval = args.synch_interval
    log_path = args.log_path

    logger = configure_logging(log_path)
    stop_path = os.path.join(source_path, "stop_sync.txt")

    while True:
        
        if os.path.exists(stop_path):
            logger.info("Synchronization stopped. Stop signal detected: {}.".format(stop_path))
            sys.exit(0)

        logger.info("Synchronization started.")    
        synch_folders(source_path, replica_path, logger)
        logger.info("Synchronization finished.")

        time.sleep(synch_interval)


if __name__ == "__main__":
    main()
