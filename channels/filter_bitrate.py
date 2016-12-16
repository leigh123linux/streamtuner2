# encoding: UTF-8
# api: streamtuner2
# title: Filter Bitrate
# description: Cleans out low-quality entries from all station lists.
# version: 0.2
# type: filter
# category: audio
# config:
#   { name: min_bitrate_mp3, value: 32, type: select, select: "32=32kbit/s|48=48kbit/s|64=64kbit/s|80=80kbit/s|96=96kbit/s|112=112kbit/s|128=128kbit/s|144=144kbit/s|160=160kbit/s", description: Filter MP3 streams with lesser audio quality. }
#   { name: min_bitrate_ogg, value: 48, type: select, select: "32=32kbit/s|48=48kbit/s|64=64kbit/s|80=80kbit/s|96=96kbit/s|112=112kbit/s|128=128kbit/s|144=144kbit/s|160=160kbit/s", description: Minimum bitrate for Ogg Vorbis and AAC. }
# priority: optional
# hooks: postprocess_filters
#
# Plugin that filters radio stations on bitrate (audio quality).
# Anything below 64 kbit/s often sounds awful for MP3 streams.
# While AAC or Ogg Vorbis might still be acceptable sometimes.
#
# This functionality was previously just implemented for the Xiph
# plugin. It's now available as generic filter for all channels.
# Beware that some channels provide more entries with low bitrates,
# thus might appear completely empty.


from config import *
from channels import GenericChannel


# Filter streams by bitrate
class filter_bitrate(object):

    meta = plugin_meta()
    module = 'filter_bitrate'

    # Hijack postprocessing filters in stream_update handler 
    def __init__(self, parent):
        GenericChannel.postprocess_filters.append(self.filter_rows)

    # Filter row on bitrate
    def filter_rows(self, row, channel):
        bits = int(row.get("bitrate", 0))
        if bits <= 10:
            return True
        elif row.get("format", channel.audioformat) in ("audio/ogg", "audio/aac", "audio/aacp"):
            return bits >= int(conf.min_bitrate_ogg)
        else:
            return bits >= int(conf.min_bitrate_mp3)

