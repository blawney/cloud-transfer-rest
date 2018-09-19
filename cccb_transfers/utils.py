import configparser

def read_config(config_filepath, additional_sections=[]):

    config = configparser.ConfigParser()
    config.read(config_filepath)

    config_dict = {}

    # read the default section:
    for key in config[config.default_section]:
        config_dict[key] =  config[config.default_section][key]

    for section_name in additional_sections:
        if section_name in config:
            d1 = {}
            section = config[section_name]
            for key in section:
                config_dict[key] = section[key]
        else:
            raise configparser.NoSectionError(section_name)

    return config_dict

def read_general_config(config_filepath, additional_sections=[]):
    config_dict = read_config(config_filepath, additional_sections)

    # Based on the choice for the compute environment, read those params also:
    try:
        compute_env = config_dict['compute_environment']
    except KeyError as ex:
        raise Exception('Your configuration file needs to define a variable named %s which indicates the cloud provider' % ex)

    config_dict.update(read_config(config_filepath, [compute_env,]))

    return config_dict
