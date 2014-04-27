#
# type: interface
# api: python
# title: PyQuery pq
# description: shortcut to PyQuery w/ extensions
#
#


import config



# load pyquery
try:

    from pyquery import PyQuery as pq

    # pq.each_pq = lambda self,func:  self.each(   lambda i,html: func( pq(html, parser="html") )   )


except Exception as e:

    # disable use
    pq = None
    config.conf.pyquery = False

    # error hint
    print("LXML is missing\n", e)
    print("\n")
    print("Please install the packages python-lxml and python-pyquery from your distributions software manager.\n")


    # let's invoke packagekit?
    """
    try:
         import packagekit.client
         pkc = packagekit.client.PackageKitClient()
         pkc.install_packages([pkc.search_name(n) for n in ["python-lxml", "python-pyquery"]])
         

    except:
        print("no LXML")
    """


