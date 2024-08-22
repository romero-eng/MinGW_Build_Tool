import os
import shutil
import platform
from typing import Optional

import flags
from command import run_command


def copy_header_files_from_source_into_include(source_directory: str,
                                               include_directory: str) -> None:

    if not os.path.exists(include_directory):
        os.mkdir(include_directory)

    for root, dirs, files in os.walk(source_directory):
        for dir in dirs:
            if not os.path.exists(dir):
                os.mkdir(dir)
        for file in files:
            if os.path.splitext(file)[1] == '.h':
                shutil.copyfile(os.path.join(source_directory, root.split(source_directory)[1], file),
                                os.path.join(include_directory, root.split(source_directory)[1], file))


def generate_object_files(source_directory: str,
                          build_directory: str,
                          build_configuration: Optional[str] = None,
                          language_standard: Optional[str] = None,
                          miscellaneous: Optional[str] = None,
                          warnings: Optional[list[str]] = None,
                          include_directories: Optional[list[str]] = None) -> bool:

    if not os.path.exists(build_directory):
        os.mkdir(build_directory)

    common_directory: str = os.path.commonpath([source_directory, build_directory])

    relative_source_directory: str = source_directory.split(f'{common_directory:s}{os.sep:s}')[1]
    relative_build_directory: str = build_directory.split(f'{common_directory:s}{os.sep:s}')[1]

    formatted_flags: list[str] = []
    if build_configuration:
        formatted_flags.append(' '.join([f'-{flag:s}' for flag in flags.get_build_configuration_flags(build_configuration)]))
    if language_standard:
        formatted_flags.append(' '.join([f'-{flag:s}' for flag in flags.get_language_standard_flag(language_standard)]))
    if warnings:
        formatted_flags.append(' '.join([f'-{flag:s}' for flag in flags.get_warning_flags(warnings)]))
    if miscellaneous:
        formatted_flags.append(' '.join([f'-{flag:s}' for flag in flags.get_miscellaneous_flags(miscellaneous)]))
    if include_directories:
        formatted_flags.append(' '.join([f'-{flag:s}' for flag in flags.get_include_directory_flags(include_directories)]))

    compile_command: str = 'g++ -c {{source_file_path:s}} -o {{object_file_path:s}} {flags:s}'
    compile_command = compile_command.format(flags=' '.join(formatted_flags))

    success: bool = True

    for root, _, files in os.walk(source_directory):
        for file in files:
            if os.path.splitext(file)[1] == '.cpp':

                success = \
                    run_command(f'"{os.path.splitext(file)[0]:s}" Compilation Results',
                                compile_command.format(source_file_path=os.path.join(relative_source_directory, root.split(source_directory)[1], file),
                                                       object_file_path=os.path.join(relative_build_directory, f'{os.path.splitext(file)[0]:s}.o')),
                                common_directory)

                if not success:
                    break

    return success


def link_object_files_into_executable(build_directory: str,
                                      executable_name: str,
                                      library_paths: Optional[list[str]] = None) -> None:

    formatted_flags: list[str] = []

    if library_paths:
        formatted_flags.append(' '.join([f'-{flag:s}' for flag in flags.get_library_flags(library_paths)]))

    link_command: str = 'g++ -o {{executable:s}} {{object_files:s}} {flags:s}'
    link_command = link_command.format(flags=' '.join(formatted_flags))
    
    run_command('Linking Results',
                link_command.format(executable=f'{executable_name:s}.exe',
                                    object_files=' '.join([file_path for file_path in os.listdir(build_directory) if os.path.splitext(file_path)[1] == '.o'])),
                build_directory)


def archive_object_files_into_static_library(library_name: str,
                                             build_directory: str,
                                             library_directory: str,
                                             other_library_paths: Optional[list[str]] = None) -> None:

    formatted_flags: list[str] = []

    if other_library_paths:
        formatted_flags.append(' '.join([f'-{flag:s}' for flag in flags.get_library_flags(other_library_paths)]))

    build_static_library_command: str = 'ar rcs {{library_path:s}} {{object_file_build_paths:s}} {flags:s}'
    build_static_library_command = build_static_library_command.format(flags=' '.join(formatted_flags))

    if not os.path.exists(library_directory):
        os.mkdir(library_directory)

    common_directory: str = \
        os.path.commonpath([build_directory,
                            library_directory])

    relative_build_directory: str = build_directory.split(f'{common_directory:s}{os.sep:s}')[1]
    relative_library_directory: str = library_directory.split(f'{common_directory:s}{os.sep:s}')[1]

    run_command('Archiving into Static Library',
                build_static_library_command.format(library_path=os.path.join(relative_library_directory,
                                                                              f'{library_name:s}.{'lib' if platform.system() == 'Windows' else 'a':s}'),
                                                    object_file_build_paths=' '.join([os.path.join(relative_build_directory, file_path) for file_path in os.listdir(build_directory) if os.path.splitext(file_path)[1] == '.o'])),
                common_directory)


def test_executable(executable_directory: str,
                    executable_name: str) -> None:

    if os.path.exists(os.path.join(os.path.join(executable_directory, f'{executable_name:s}.exe'))):
        _ = \
            run_command('Testing Executable',
                        f'{executable_name:s}.exe',
                        executable_directory)


def build_static_library_from_source(source_directory: str,
                                     build_directory: str,
                                     include_directory: str,
                                     library_directory: str,
                                     library_name: str,
                                     build_configuration: Optional[str] = None,
                                     language_standard: Optional[str] = None,
                                     miscellaneous: Optional[str] = None,
                                     warnings: Optional[list[str]] = None,
                                     include_directories: Optional[list[str]] = None,
                                     library_paths: Optional[list[str]] = None) -> None:

        success: bool = \
            generate_object_files(source_directory,
                                  build_directory,
                                  build_configuration,
                                  language_standard,
                                  miscellaneous,
                                  warnings,
                                  include_directories)

        if success:

            copy_header_files_from_source_into_include(source_directory,
                                                       include_directory)

            archive_object_files_into_static_library(library_name,
                                                     build_directory,
                                                     library_directory,
                                                     library_paths)


def build_executable_from_source(source_directory: str,
                                 build_directory: str,
                                 executable_name: str,
                                 build_configuration: Optional[str] = None,
                                 language_standard: Optional[str] = None,
                                 miscellaneous: Optional[str] = None,
                                 warnings: Optional[list[str]] = None,
                                 include_directories: Optional[list[str]] = None,
                                 library_paths: Optional[list[str]] = None) -> None:

    success: bool = \
        generate_object_files(source_directory,
                              build_directory,
                              build_configuration,
                              language_standard,
                              miscellaneous,
                              warnings,
                              include_directories)

    if success:
        link_object_files_into_executable(build_directory,
                                          executable_name,
                                          library_paths)

    test_executable(build_directory, executable_name)
