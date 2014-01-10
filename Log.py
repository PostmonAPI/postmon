#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime

import os

class Log():
    
    def __init__(self):
        self.file_log_path = os.environ.get('POSTMON_LOG_DIR')
        
    def cep_log_write(self, text):
        today = datetime.now()
        
        with open(self.file_log_path + 'cep_tracker.log', 'a') as log_file:
            text_line = '{0}/{1}/{2} - {3}:{4} --- {5}\n'.format(today.day, 
                    today.month, today.year, today.hour, today.minute, text)

            log_file.write(text_line)
