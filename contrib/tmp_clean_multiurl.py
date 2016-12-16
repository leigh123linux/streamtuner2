# encoding: utf-8
# title: TMP: clean Multi-URLs
# description: Strips multiple stream URLs from stations (for RadioSure mostly)
# version: 0.1
# depends: streamtuner2 >= 2.2.0, streamtuner2 < 2.2.1
# type: feature
# category: filter
#
# While action.py does not yet support space-separated URL lists in station
# entries, this plugin cleans them up. It strips anything but the first URL.


import re
from channels import GenericChannel
from config import log, conf


# filter
class tmp_clean_multiurl(object):
    module = 'tmp_clean_multiurl'
    rx_space = re.compile(r"\s")
    rx_nonurl = re.compile(r"(^|\s)(?!\w+:)\S+")

    # Hook
    def __init__(self, parent):
        GenericChannel.postprocess_filters.append(self.filter_rows)

    # does not omit any rows, just updated `url` field
    def filter_rows(self, row, channel):
        urls = row.get("url", "")
        if re.search(self.rx_space, urls):
            urls = urls.strip()
            urls = re.sub(self.rx_nonurl, "", urls)
            row["url"] = urls.strip().split(" ")[0]
        return True
