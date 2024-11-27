
* have the Python script load up a page from a HTML index file that is a PureScript app with some JS glue (e.g. for registering channels)
* auto-build the PureScript. See if there is a way to get the app to refresh
* see what the performance of D3 rendering is like in the app


I updated the flaming-octo-happiness repo a few hours ago with some new example scripts that demonstrate the embedded browser viewing
1. slippy map with vector layer;
1. PDF viewer.

I verified that this ran for me with Python 3.13 on my Mac. Please try and get these running on your machine. Although the goal is to have these running on Windows under Excel, it seems way easier in terms of setup to do the brunt of the development work on the Mac as that is what  a lot of people seem to be using and the installation-related considerations for PyXLL and Excel etc are quite burdensome.

There are a few formats of data that come to mind for these experiments and they each have differing requirements in terms of the interaction model:
* geospatial -> maps and overlays
* tabular in web pages
* PDF documents


## e-mails
## tables from database queries
I will start with maps because I think they are a bit easier to talk about:
. I want to be able to zoom and pan around the map and have those events controlled by  Python/Excel  either by being written back to Excel or by Excel/Python setting up Javascript handlers that call stuff that has been set up on a webchannel
. if the map has boundary/shape/geometry data and there are some data attributes associated with it, I would like to be able to get/set those attributes from Python. Similarly for hover, tooltip, click, righ-click
. Update the map with geospatial and tabular data as the spreadsheet changes.

### PDF documents:
table extraction driven by similar tables in the spreadsheet e.g. if we have 4 column table with date, currency, currency, number then look for both similarly structured tables in the PDF, and tables with similar structure *and* similar contents 
annotations. If we have an LLM that can answer questions with page numbers and bounding boxes then it would be nice to draw annotations on the PDF dynamically using data from the spreadsheet (use alpha transparency to help with soundness-checking the answer)

### Tables in HTML:
do a JOIN with table in spreadsheet; show similarities; show differences; 
extract tables from spreadsheet; extract list/tree of tables as a JSON blob (to be distributed on the spreadsheet by jmespath expressions)
add columns to HTML tables based on columns in the spreadsheet

### e-mails/troubleticketing systems
CTP view for people to check stuff and perhaps to update metadata (e.g. prioritization)

That's enough to be going on with for now. I am going to concentrate on the how to interface with the DOM (HTML; CSS; JavaScript) with a view to figuring out balance between putting in specialized code that can be called from Python or whether to use the webchannel stuff to call stuff directly (in either direction). I do not know yet what kind of interaction model is preferable but will probably find out very quickly when I start writing test applications.
