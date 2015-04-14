# api: streamtuner2
# title: Bieber
# description: Bieber music
# url: http://www.justinbiebermusic.com/
# version: 5.2
# type: channel
# category: example
# config: 
#     { "name": "bieber_filter", "type": "text", "value": "BIEBERBLAST", "description": "So and so." }
# priority: joke
#
# This was an entertaining test plugin for development. (Compound function
# went into the search feature, and the compound channel plugin obviously.)
#
# It's however a very simple plugin, and hence a good basis for writing
# your own extensions.


from channels import *


# Bieber music filter plugin
class bieber(ChannelPlugin):


    # config data
    config = [
    ]
    

    # category map
    categories = ['the Biebs']
    default = 'the Biebs'
    current = 'the Biebs'




    # static category list
    def update_categories(self):
        # nothing to do here
        pass


    # just runs over all channel plugins, and scans their streams{} for matching entries
    def update_streams(self, cat, force=0):

        # result list
        entries = []
        
        # kill our current list, so we won't find our own entries
        self.streams = {}
        
        # swamp through all plugins
        for name,p in self.parent.channels.iteritems():
            #print "bieberquest: channel", name

            # subcategories in plugins        
            for cat,stations in p.streams.iteritems():
                #print "   bq cat", cat
            
                # station entries
                for row in stations:

                    # collect text fields, do some typecasting, lowercasing
                    text = "|".join([str(e) for e in row.values()])
                    text = text.lower()

                    # compare
                    if text.find("bieb") >= 0:
                    
                        # add to result list
                        row["genre"] = name + ": " + row.get("genre", "")
                        entries.append(row)

        # return final rows list
        return entries
        


