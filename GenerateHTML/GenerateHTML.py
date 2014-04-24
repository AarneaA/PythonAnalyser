from datetime import datetime, timedelta
from os import listdir, path, makedirs
import ast

def getlineinfo(line):
    linedict = {}
    timestamp = line[-27:-1]
    timestamp = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f")
    eventclass = line[0:15].split("(")[0]
    linelist = line[len(eventclass)+1:-32].split(",",4)
    for pair in linelist:
        if(pair.split("=",1)[0][0] == " "):
            linedict[pair.split("=",1)[0][1:]] = pair.split("=",1)[1][1:-1]
        else:
            linedict[pair.split("=",1)[0]] = pair.split("=",1)[1][1:-1]
    linedict['class'] = eventclass
    linedict['time'] = timestamp
    return linedict

def getlineinfotags(line):
    linedict = {}
    timestamp = line[-27:-1]
    timestamp = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f")
    eventclass = line[0:15].split("(")[0]
    linelist = line[len(eventclass)+1:-32].split(",",3)
    for pair in linelist:
        if(pair.split("=",1)[0][0] == " "):
            linedict[pair.split("=",1)[0][1:]] = pair.split("=",1)[1][1:-1]
        else:
            linedict[pair.split("=",1)[0]] = pair.split("=",1)[1][1:-1]
    linedict['class'] = eventclass
    linedict['time'] = timestamp
    return linedict

def getstats(logfilename):
    editors = geteditorids(logfilename)
    filenames = {}
    typeamt = 0
    pasteamt = 0
    runamt = 0
    erramt = 0
    starttime = None
    endtime = None
    losefocusamt = 0
    stats = [["Time"]]
    #Get file names, match them with editor ids
    with open("../user_logs/" + str(logfilename)) as logfile:
        for line in logfile:
            if(line[0:4] == 'Load' or line[0:6] == 'SaveAs'):
                lineinfo = getlineinfo(line)
                if(lineinfo['editor_id'] not in filenames):
                    filenames[lineinfo['editor_id']] = lineinfo['filename'].split(r"\\")[-1]
            if(len(filenames) == len(editors)):
                break
    if(len(editors) > len(filenames)):
        for editor in editors:
            if(editor not in filenames):
                filenames[str(editor)] = 'untitled'
    #Initialize stats list
    for editor in editors:
        stats[0].append(filenames[str(editor)])
    #Get code additions per editor/file
    with open("../user_logs/" + str(logfilename)) as logfile:    
        for line in logfile:
            lineinfo = getlineinfo(line)
            if(starttime == None):
                starttime = lineinfo['time']
            endtime = lineinfo['time']
            if(line[0:10] == "TextInsert"):
                if(lineinfo['tags'] == 'None'):
                    if(lineinfo['editor_id'] in editors):
                        if(lineinfo['source'] == 'PasteEvent'):
                            pasteamt += len(lineinfo['text'])
                        elif(lineinfo['source'] == 'KeyPressEvent'):
                            typeamt += len(lineinfo['text'])
                        #Generate addition
                        addition = [""]
                        for i in range(1,len(editors)+1):
                            if(len(stats)>1):
                                addition.append(stats[-1][i])
                            else:
                                addition.append(0)
                        if(len(stats) > 1):
                            addition[editors.index(lineinfo['editor_id'])+1] = stats[-1][editors.index(lineinfo['editor_id'])+1] + len(lineinfo['text'])
                            stats.append(addition)
                        else:
                            addition[editors.index(lineinfo['editor_id'])+1] = len(lineinfo['text'])
                            stats.append(addition)
                else:
                    lineinfotags = getlineinfotags(line)
                    if('error' in lineinfotags['tags']):
                        erramt += 1
            elif(line[0:10] == "TextDelete"):
                if(lineinfo['editor_id'] in editors):
                    #Generate deletion
                    deletion = [""]
                    for i in range(1,len(editors)+1):
                        if(len(stats)>1):
                            deletion.append(stats[-1][i])
                        else:
                            deletion.append(0)
                    if (len(stats) > 1):
                        from_colno = int(lineinfo['from_position'].split(".")[1])
                        to_colno = int(lineinfo['to_position'].split(".")[1])
                        deletion[editors.index(lineinfo['editor_id'])+1] = stats[-1][editors.index(lineinfo['editor_id'])+1] - (from_colno-to_colno)
                        stats.append(deletion)
            elif(lineinfo['class'] == 'EditorLoseFocus'):
                losefocusamt += 1
            elif(lineinfo['class'] == 'Command' and (lineinfo['cmd_id'] == 'run_current_script' or lineinfo['cmd_id'] == 'debug_current_script')):
                runamt += 1
    return stats, pasteamt, typeamt, losefocusamt, runamt, erramt, starttime, endtime


def geteditorids(logfilename):
    editors = []
    with open("../user_logs/" + str(logfilename)) as logfile:
       for line in logfile:
           lineinfo = getlineinfo(line)
           if('editor_id' in lineinfo and lineinfo['editor_id'] not in editors and lineinfo['class'] != 'ShellCreate'):
                if('tags' in lineinfo):
                    if(lineinfo['tags'] == 'None'):
                        editors.append(lineinfo['editor_id'])
    return editors
               
def generatehtml(stats, pasteamt, typeamt, losefocusamt, runamt, erramt, startdate, enddate, logfilename):
    html = """
<html>
  <head>
  <link rel="stylesheet" href="style.css">
    <script type="text/javascript" src="https://www.google.com/jsapi"></script>
    <script type="text/javascript">
      google.load("visualization", "1", {packages:["corechart"]});
      google.setOnLoadCallback(drawChart);
	  google.setOnLoadCallback(drawChart2);
      function drawChart() {
        var data = google.visualization.arrayToDataTable(
		"""+ str(stats) +""");
        var options = {
          title: 'Code length in characters over time'
        };

        var chart = new google.visualization.LineChart(document.getElementById('Line_chart'));
        chart.draw(data, options);
		var chart2 = new google.visualization.LineChart(document.getElementById('second_chart'));
        chart2.draw(data, options);
      }
	  function drawChart2() {
        var data = google.visualization.arrayToDataTable([
          ['Source', 'Characters'],
          ['Written',     """ + str(typeamt) + """],
          ['Pasted',      """ + str(pasteamt) + """],
        ]);
        var options = {
          title: 'Ratio of written and pasted code'
        };
        var chart = new google.visualization.PieChart(document.getElementById('Pie_chart'));
        chart.draw(data, options);
      }	  
    </script>
  </head>
  <body>
  <div class=bodyc>
	<div class=upper>
	<div class=header> <h1>"""+ str(logfilename) + """</h1></div>
	</div>	
	<div class=middle>
	<div class=data>
	<TABLE>
	<TR>
	<TD class=key>Number of runs:</TD>
	<TD class=value>""" + str(runamt) + """</TD>
	<TD class=key> Number of focus loss: </TD>
	<TD class=value>""" + str(losefocusamt) + """</TD>
	</TR>
	<TR>
	<TD class=key> Number of unsucessful runs: </TD>
	<TD class=value>""" + str(erramt) + """ </TD>
	<TD> </TD>
	<TD> </TD>
	</TR>
	<TR>
	<TD class=key>Start date:</TD>
	<TD class=value>""" + str(startdate)[:-7] + """</TD>
	<TD class=key>End date:</TD>
	<TD class=value>""" + str(enddate)[:-7] + """</TD>
	</TR>
	</TABLE>
	</div>
	
    <div id="Line_chart" class=chart "></div>
	<div id="Pie_chart" class=chart></div>
	</div>
	</div>

	
  </body>
</html>
"""
    
    try:
        htmlfile = open(str(logfilename[:-4]) + ".html", 'x')
        htmlfile.write(html)
        htmlfile.close()
    except:
        pass

    return None

def generateindex(logfiles):
    html = """
<html>
  <head>
  <link rel="stylesheet" href="style.css">
  </head>
  <body>
  <div class=bodyc>
	<div class=upper>
	<div class=header> <h1>Index page</h1></div>
	</div>
	<div class=middle>
	
	"""
    for log in logfiles:
        html = html + "<a href=\"" + str(log[:-4]) + ".html\">" + str(log[:-4]) + "</a><br>" 
    html = html +"""
	</div>
	</div>	
  </body>
</html>
    """
    htmlfile = open("index.html" , 'w')
    htmlfile.write(html)
    htmlfile.close()
    return None

logfiles = listdir("../user_logs")

for Logfilename in logfiles:
    editors = geteditorids(Logfilename)

    stats, pasteamt, typeamt, losefocusamt, runamt, erramt, startdate, enddate = getstats(Logfilename)
    generatehtml(stats, pasteamt, typeamt, losefocusamt, runamt, erramt, startdate, enddate, Logfilename)

generateindex(logfiles)

