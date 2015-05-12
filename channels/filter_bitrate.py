# encoding: UTF-8
# api: streamtuner2
# title: Filter Bitrate
# description: Cleans up low-quality entries from all station lists.
# version: 0.1
# type: filter
# category: audio
# priority: optional
# config:
#   { name: min_bitrate_mp3, value: 32, type: select, select: "32|48|64|80|96|112|128|144|160", description: Filter MP3 streams with lesser audio quality. }
#   [ name: min_bitrate_ogg, value: 32, type: select, select: "32|48|64|80|96|112|128|144|160", description: OggVorbis/AAC sound ok with slightly lower bitrates still. ]
# hooks: -
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
import channels


# Filter streams by bitrate
class filter_bitrate():

    meta = plugin_meta()
    module = "filter_bitrate"

    # Hijack GenericChannel.prepare
    def __init__(self, parent):
        channels.GenericChannel.postprocess_filters.append(self.filter_rows)

    # filter bitrate
    def filter_rows(self, row):
        b = int(row.get("bitrate", 0))
        if b <= 10:
            return True
        elif b < int(conf.min_bitrate_mp3):
            return False
        else:
            return True

