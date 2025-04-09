#chatlab/colnames

            # Assumed column names at conversation level
colnames = {'conv': {'conv_id': 'conv_id',
                     'user_id': 'user_id',
                     'user_freq': 'user_freq',
                     'conversation': 'conversation',
                     'source': 'source',
                     'model': 'model',
                     'country': 'country',
                     'state': 'state',
                     'turns': 'turns',
                     'n_code': 'n_code',
                     'n_toxic': 'n_toxic',
                     'n_redacted': 'n_redacted',
                     'start': 'time_first',
                     'end': 'time_last',
                     'n_words': 'n_words',
                     'n_words_user': 'n_words_user',
                     'n_words_gpt': 'n_words_gpt',
                     'language': 'language'},
            # Assumed column names at turn level
            'turn': {'conv_id': 'conv_id',
                     'role': 'role',
                     'turn_number': 'turn_num',
                     'message': 'content',
                     'language': 'language',
                     'n_words': 'n_words',
                     'code_block': 'code_block', # only rows where role == 'assistant'
                     'toxic': 'toxic',
                     'redacted': 'redacted',
                     'timestamp': 'timestamp'} # Only rows where role == 'assistant
            }

