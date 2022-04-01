#! /usr/bin/env python3

import argparse
import pathlib
import sys
import G2Paths
from G2Config import G2Config
from G2ConfigMgr import G2ConfigMgr
from G2IniParams import G2IniParams
from G2Exception import G2ModuleException


def setup_config(ini_params, auto_mode):

    # Determine if a default/initial G2 configuration already exists
    default_config_id = bytearray()
    g2_config_mgr = G2ConfigMgr()
    g2_config_mgr.initV2("g2ConfigMgr", ini_params, False)
    g2_config_mgr.getDefaultConfigID(default_config_id)

    # If not in auto mode prompt user
    if not auto_mode:

        if default_config_id:
            if not input('\nA configuration document already exists in the database. Do you want to replace it (yes/no)?  ') in ['y', 'Y', 'yes', 'YES']:
                print('\nWARN: Not replacing configuration in database.')
                return -1
        else:
            if not input('\nInstalling template configuration to database. Do you want to continue (yes/no)?  ') in ['y', 'Y', 'yes', 'YES']:
                print('\nWARN: No default template configuration has been applied to the database.')
                return -1

    # Apply a default configuration
    g2_config = G2Config()
    g2_config.initV2("g2Config", ini_params, False)

    try:
        config_handle = g2_config.create()
    except G2ModuleException as ex:
        print('\nERROR: Could not get template config from G2Config.')
        print(f'\n\t{ex}')
        return -1

    new_configuration_bytearray = bytearray()
    g2_config.save(config_handle, new_configuration_bytearray)
    g2_config.close(config_handle)

    config_json = new_configuration_bytearray.decode()

    # Save configuration JSON into G2 database.
    new_config_id = bytearray()

    try:
        g2_config_mgr.addConfig(config_json, 'Configuration added from G2SetupConfig.', new_config_id)
    except G2ModuleException as ex:
        ex_info = g2_config_mgr.getLastException().split('|', 1)
        # The engine configuration compatibility version [{0}] does not match the version of the provided config[{1}]
        if ex_info[0] == '0040E':
            print("\nERROR: Failed to add config to the database. Please ensure your config is updated to the current version.")
        else:
            print("\nERROR: Failed to add config to the datastore.")
        print(f'\n\t{ex}')
        return -1

    # Set the default configuration ID.
    try:
        g2_config_mgr.setDefaultConfigID(new_config_id)
    except G2ModuleException as ex:
        print("\nERROR: Failed to set config as default.")
        print(f'\n\t{ex}')
        return -1

    # Shut down
    g2_config_mgr.destroy()
    g2_config.destroy()

    print("\nConfiguration successfully added.")

    return 0


if __name__ == '__main__':

    argParser = argparse.ArgumentParser()
    argParser.add_argument('-c',
                           '--iniFile',
                           default=None,
                           help='Path and file name of optional G2Module.ini to use.',
                           nargs=1)

    # Run in non-interactive mode for Senzing team testing
    argParser.add_argument('-a',
                           '--auto',
                           action='store_true',
                           help=argparse.SUPPRESS)

    args = argParser.parse_args()

    # If ini file isn't specified try and locate it with G2Paths
    ini_file_name = pathlib.Path(G2Paths.get_G2Module_ini_path()) if not args.iniFile else pathlib.Path(args.iniFile[0]).resolve()
    G2Paths.check_file_exists_and_readable(ini_file_name)

    # Load the G2 configuration file
    ini_param_creator = G2IniParams()
    ini_params = ini_param_creator.getJsonINIParams(ini_file_name)

    sys.exit(setup_config(ini_params, args.auto))
