from configparser import ConfigParser

def read_config(config_filepath):

    cfg = ConfigParser()
    cfg.read(config_filepath)
    
    config_dict = {}

    # read the default params:
    for key in cfg['DEFAULT']:
        config_dict[key] =  cfg['DEFAULT'][key]

    # Based on the choice for the compute environment, read those params also:
    try:
        compute_env = config_dict['compute_environment']
    except KeyError as ex:
        raise Exception('Your configuration file needs to define a variable named %s which indicates the cloud provider' % ex)

    try:
        section = cfg[compute_env]
    except KeyError as ex:
        raise Exception('''
            Your configuration file needs to declare section named %s which 
            provides the required parameters for your selected compute environment.''' % ex)
    for key in section:
            config_dict[key] = section[key]

    return config_dict
