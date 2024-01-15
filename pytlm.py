import os
import matplotlib.pyplot as plt
import pandas as pd

import logging

def create_custom_logger(name: str, level=logging.DEBUG):
    logger = logging.getLogger(name)
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    logger.setLevel(level)
    return logger

class Log():
    log = create_custom_logger('Log', logging.INFO)

    def __init__(self, log_folder, resample=True, resample_interval='1000us', align='none', ignore_networks=[], consider_networks=[]):
        if not os.path.exists(log_folder):
            raise FileNotFoundError(f"Log folder {log_folder} does not exist")
        if not os.path.isdir(log_folder):
            raise FileNotFoundError(f"Log folder {log_folder} is not a directory")
        if len(ignore_networks) > 0 and len(consider_networks) > 0:
            raise ValueError("Cannot ignore and consider networks at the same time")
        
        self.root = log_folder
        self.name = log_folder.split('/')[-1] if log_folder[-1] != '/' else log_folder.split('/')[-2]

        self.data = {}

        self.empty_messages = {}
        self.n_empty_messages = 0
        self.error_messages = {}
        self.n_error_messages = 0
        self.null_messages = {}
        self.n_null_messages = 0
        self.out_of_sync_messages = {}
        self.n_out_of_sync_messages = 0
        
        Log.log.info(f'Loading log {self.name}')
        for network in os.listdir(os.path.join(log_folder, 'parsed')):
            if network in ignore_networks:
                continue
            if len(consider_networks) > 0 and network not in consider_networks:
                continue

            self.data[network] = {}
            for message_filename in os.listdir(os.path.join(log_folder, 'parsed', network)):
                if message_filename.endswith('.csv'):
                    message = message_filename.split('.')[0]
                    try:                    
                        df = self._dataframe_from_csv(os.path.join(self.root, 'parsed', network, message_filename))
                    except pd.errors.EmptyDataError:
                        if network not in self.empty_messages.keys():
                            self.empty_messages[network] = []
                        self.empty_messages[network].append(message)
                        self.n_empty_messages += 1
                        continue
                    except MemoryError as e:
                        if network not in self.error_messages.keys():
                            self.error_messages[network] = []
                        self.error_messages[network].append((message, e))
                        self.n_error_messages += 1
                        continue

                    # remove null values
                    df, n_null_values = self._remove_null_values(df)
                    if n_null_values > 0:
                        if network not in self.null_messages.keys():
                            self.null_messages[network] = []
                        self.null_messages[network].append((message, n_null_values))
                        self.n_null_messages += 1

                    # resample
                    if resample:
                        try:
                            df = self._resample(df, resample_interval)
                        except TypeError as e:
                            if network not in self.error_messages.keys():
                                self.error_messages[network] = []
                            self.error_messages[network].append((message, e))
                            self.n_error_messages += 1
                            continue

                    # add dataframe to data structure if everything went fine
                    self.data[network][message] = df
            
        self._align_timestamps(align)

        Log.log.info(f'====================== {self.name} integrity report ======================')
        
        if self.n_empty_messages == 0 and self.n_error_messages == 0 and self.n_null_messages == 0 and self.n_out_of_sync_messages == 0:
            Log.log.info(f'No integrity issues found in log {self.name}')
        else:
            if self.n_empty_messages > 0:
                Log.log.info(f'{self.n_empty_messages} empty messages have been ignored:')
                for network in self.empty_messages.keys():
                    Log.log.info(f'\t{len(self.empty_messages[network])} in network {network}:')
                    self.empty_messages[network].sort()
                    for i, message in enumerate(self.empty_messages[network]):
                        Log.log.info(f'\t\t{i+1} : {message}')

            if self.n_error_messages > 0:
                Log.log.info(f'{self.n_error_messages} messages could not be loaded due to errors:')
                for network in self.error_messages.keys():
                    Log.log.info(f'\t{len(self.error_messages[network])} in network {network}:')
                    self.error_messages[network].sort()
                    for i, (message, error) in enumerate(self.error_messages[network]):
                        Log.log.info(f'\t\t{i+1} : {message} with error: \"{error}\"')

            if self.n_null_messages > 0:
                Log.log.info(f'{self.n_null_messages} messages have been cleared of null values:')
                for network in self.null_messages.keys():
                    Log.log.info(f'\t{len(self.null_messages[network])} in network {network}:')
                    self.null_messages[network].sort()
                    for i, (message, n_null_values) in enumerate(self.null_messages[network]):
                        Log.log.info(f'\t\t{i+1} : {message} with {n_null_values} null values')

            if self.n_out_of_sync_messages > 0:
                Log.log.info(f'{self.n_out_of_sync_messages} messages are empty after aligning timestamps:')
                for network in self.out_of_sync_messages.keys():
                    Log.log.info(f'\t{len(self.out_of_sync_messages[network])} in network {network}:')
                    self.out_of_sync_messages[network].sort()
                    for i, message in enumerate(self.out_of_sync_messages[network]):
                        Log.log.info(f'\t\t{i+1} : {message}')

        Log.log.info(f'==========================================================================\n')

    def get_networks_list(self):
        return list(self.data.keys())
    
    def get_messages_list(self, network):
        if network not in self.get_networks_list():
            raise KeyError(f"Network {network} not found in log {self.name}")
        
        return list(self.data[network].keys())
    
    def get_payloads_list(self, network, message):
        if network not in self.get_networks_list():
            raise KeyError(f"Network {network} not found in log {self.name}")
        
        if message not in self.get_messages_list(network):
            if network in self.out_of_sync_messages.keys() and message in self.out_of_sync_messages[network]:
                err = f'Message {message} not found in network {network} in log {self.name}. Was deleted after aligning timestamps'
            elif network in self.empty_messages.keys() and message in self.empty_messages[network]:
                err = f'Message {message} not found in network {network} in log {self.name}. Was empty at import'
            elif network in self.error_messages.keys() and message in self.error_messages[network]:
                err = f'Message {message} not found in network {network} in log {self.name}. Could not be loaded due to error'
            else:
                err = f'Message {message} not found in network {network} in log {self.name}'
            raise KeyError(err)
        
        return self.data[network][message].columns
    
    def get(self, network=None, message=None, payload=None):
        if network is None:
            return self.data
        
        if message is None:
            if network not in self.get_networks_list():
                raise KeyError(f"Network {network} not found in log {self.name}")
            
            return self.data[network]
        
        if payload is None:
            if message not in self.get_messages_list(network):
                if network in self.out_of_sync_messages.keys() and message in self.out_of_sync_messages[network]:
                    err = f'Message {message} not found in network {network} in log {self.name}. Was deleted after aligning timestamps'
                elif network in self.empty_messages.keys() and message in self.empty_messages[network]:
                    err = f'Message {message} not found in network {network} in log {self.name}. Was empty at import'
                elif network in self.error_messages.keys() and message in self.error_messages[network]:
                    err = f'Message {message} not found in network {network} in log {self.name}. Could not be loaded due to error'
                else:
                    err = f'Message {message} not found in network {network} in log {self.name}'
                raise KeyError(err)
        
            return self.data[network][message]
        
        if payload not in self.get_payloads_list(network, message):
            raise KeyError(f"Payload {payload} not found in message {message} in network {network} in log {self.name}")
        
        return self.data[network][message][payload]
    
    def quick_plot(self, network, message, payload):
        plt.figure()
        plt.title(f'{network} - {message} - {payload}')
        plt.plot(self.get(network, message, payload), label=payload)
        plt.legend(loc='upper right')
        plt.show()
        
    def _resample(self, df: pd.DataFrame, interval: str):
        df = df.resample(interval).mean().interpolate()
        return df

    def _dataframe_from_csv(self, csv_path):
        df = pd.read_csv(csv_path)

        if len(df) == 0:
            raise pd.errors.EmptyDataError("Empty dataframe")

        df['_timestamp'] = pd.to_datetime(df['_timestamp'], unit='us')
        df = df.drop_duplicates(subset=['_timestamp'])
        df = df.set_index('_timestamp')

        return df
    
    def _remove_null_values(self, df):
        n_null_values = df.isnull().values.sum()
        if n_null_values > 0:
            # drop any row that has any null value
            df = df.dropna(how='any')

        return df, n_null_values

    def _align_timestamps(self, how = 'both'):
        compatible_how = ['both', 'beginning', 'end', 'none']
        if how not in compatible_how:
            raise ValueError(f"Invalid value for parameter how: {how}. Use one of {compatible_how}")
        
        out_of_sync_messages = {}
        n_out_of_sync_messages = 0

        if how == 'none':
            return n_out_of_sync_messages, out_of_sync_messages

        align_beginning = True if how == 'both' or how =='beginning' else False
        align_end = True if how == 'both' or how =='end' else False


        if align_beginning:
            max_min_timestamp = None # The minimum of the maximum timestamps of all messages
            min_min_timestamp = None

        if align_end:
            min_max_timestamp = None # The maximum of the minimum timestamps of all messages
            max_max_timestamp = None

        Log.log.info(f"Aligning timestamps to {how}...")
        is_first_iteration = True
        for network in self.get_networks_list():
            for message in self.get_messages_list(network):
                message = self.get(network, message)
                current_min_timestamp = message.index.min()
                current_max_timestamp = message.index.max()
                if is_first_iteration:
                    max_min_timestamp = current_min_timestamp
                    min_max_timestamp = current_max_timestamp
                    min_min_timestamp = current_min_timestamp
                    max_max_timestamp = current_max_timestamp
                    is_first_iteration = False

                if align_beginning:
                    max_min_timestamp = max(max_min_timestamp, current_min_timestamp)
                    min_min_timestamp = min(min_min_timestamp, current_min_timestamp)
                if align_end:
                    min_max_timestamp = min(min_max_timestamp, current_max_timestamp)
                    max_max_timestamp = max(max_max_timestamp, current_max_timestamp)


        for network in self.get_networks_list():
            for message in self.get_messages_list(network):
                if align_beginning and align_end:
                    self.data[network][message] = self.get(network, message).loc[max_min_timestamp:min_max_timestamp]
                elif align_beginning:
                    self.data[network][message] = self.get(network, message).loc[max_min_timestamp:]
                elif align_end:
                    self.data[network][message] = self.get(network, message).loc[:min_max_timestamp]
                
                if len(self.data[network][message]) == 0:
                    if network not in out_of_sync_messages.keys():
                        out_of_sync_messages[network] = []
                    out_of_sync_messages[network].append(message)
                    n_out_of_sync_messages += 1
                    # remove empty message
                    self.data[network].pop(message)

        if align_beginning and align_end:
            Log.log.info(f"Timestamps aligned at {max_min_timestamp} : {min_max_timestamp}. {n_out_of_sync_messages} messages were dropped, {max_min_timestamp - min_min_timestamp} removed from beginning, {max_max_timestamp - min_max_timestamp} removed from end")
        elif align_beginning:
            Log.log.info(f"Timestamps aligned at beginning at {max_min_timestamp}. {n_out_of_sync_messages} messages were dropped, {max_min_timestamp - min_min_timestamp} removed from beginning")
        elif align_end:
            Log.log.info(f"Timestamps aligned at end at {min_max_timestamp}. {n_out_of_sync_messages} messages were dropped, {max_max_timestamp - min_max_timestamp} removed from end")

        Log.log.info(f'log lasts {min_max_timestamp - max_min_timestamp}')
        
        self.n_out_of_sync_messages = n_out_of_sync_messages
        self.out_of_sync_messages = out_of_sync_messages