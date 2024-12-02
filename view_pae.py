import sys

myf = open(sys.argv[2], "r")
o = myf.read()
myf.close()

html_content = f"""
<html>
    <body>
        {o}
    </body>
</html>
"""

import webview
webview.create_window(sys.argv[1], html=html_content, width=1400) #, y=y)
webview.start()