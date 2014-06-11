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
#Temporary workaround
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

def getimportanttimes(editor, logfilename):
    timestamps = []
    with open("../user_logs/" + str(logfilename)) as logfile:
        for line in logfile:
            lineinfo = getlineinfo(line)
            if('editor_id' in lineinfo and editor == lineinfo['editor_id']):
                if(lineinfo['class'] == 'Save' or lineinfo['class'] == 'SaveAs' or lineinfo['class'] == 'EditorLoseFocus'):
                    timestamps.append(lineinfo['time'])
            elif(lineinfo['class'] == 'Command'):
                if(lineinfo['cmd_id'] == 'run_current_script' or lineinfo['cmd_id'] == 'debug_current_script'):
                    timestamps.append(lineinfo['time'])
    return timestamps
            
def getsnapshot(editor, time, filename):
    snapshot = ""
    lines = []
    sourceline = ""
    with open(filename, encoding='utf-8') as logfile:
        firsttimestamp = None
        for line in logfile:
            if(firsttimestamp == None):
                firsttimestamp = line[-27:-1]
                firsttimestamp = datetime.strptime(firsttimestamp, "%Y-%m-%dT%H:%M:%S.%f")
            if(line[0:10] == "TextInsert"):
                lineinfo = getlineinfo(line)
                if(lineinfo['editor_id'] == editor and lineinfo['source']=='LoadEvent'):
                    lines=lineinfo['text'].split(r"\n")
                elif (lineinfo['editor_id'] == editor and lineinfo['time']<= time):
                    lineno = int(lineinfo['position'].split(".")[0])
                    colno = int(lineinfo['position'].split(".")[1])+1
                    if(lineinfo['text'] == r"\n" or lineinfo['text'] == r"\n    "):
                        colno -= 1
                    lineinfo['text'] = lineinfo['text'].replace(r"\t", "    ")
                    lineinfo['text'] = lineinfo['text'].replace(r"\n", " \n")
                    lineinfo['text'] = lineinfo['text'].replace("\ \n", r"\n")
                    lineinfo['text'] = lineinfo['text'].replace(r"\\", "\\")
                    if(lineno > len(lines)):
                        #for line in reversed(lineinfo['text'].split(r"\n")):
                        for line in reversed(lineinfo['text'].splitlines()):
                            lines.insert(lineno-1, line)

                    else:
                        if(lineinfo['source'] == 'PasteEvent' or lineinfo['source'] == 'RedoEvent' or lineinfo['source'] == 'UndoEvent'):
                            lines[lineno-1] = lines[lineno-1][:colno-1] + lineinfo['text'] + lines[lineno-1][colno-1:]
                            #insertedlines = lines[lineno-1].split(r"\n")
                            insertedlines = lines[lineno-1].splitlines()
                            insertedlines.reverse()
                            for insertedline in insertedlines[:-1]:
                                   lines.insert(lineno, insertedline)
                            #lines[lineno-1] = lines[lineno-1].split(r"\n")[0]
                            lines[lineno-1] = lines[lineno-1].splitlines()[0]
                        else:
                            lines[lineno-1] = lines[lineno-1][:colno-1] + lineinfo['text'] + lines[lineno-1][colno-1:]
                            if("\n" in lines[lineno-1]):

                                #Changed from splitlines to split \n
                                lines.insert(lineno, lines[lineno-1].split("\n")[1])
                                lines[lineno-1] = lines[lineno-1].splitlines()[0]                  
            elif(line[0:10] == "TextDelete"):
                lineinfo = getlineinfo(line)     
                if (lineinfo['editor_id'] == editor and lineinfo['time']< time and lineinfo['source'] != 'LoadEvent'):         
                    lineno = int(lineinfo['from_position'].split(".")[0])
                    to_lineno = int(lineinfo['to_position'].split(".")[0])
                    #lineno, to_lineno = to_lineno, lineno
                    from_colno = int(lineinfo['from_position'].split(".")[1])
                    to_colno = int(lineinfo['to_position'].split(".")[1])
                    #Try catch in case of empty lines list
                    try:
                        while(to_colno > len(lines[lineno]) and to_lineno < len(lines)):
                            to_colno -= len(lines[to_lineno-1])
                            to_lineno += 1
                    except:
                        pass
                    if(lineno != to_lineno):
                        if(len(lines)!=0):
                            lines[lineno-1] = lines[lineno-1][:from_colno] + lines[to_lineno-1][to_colno:]
                            if(to_colno != len(lines[to_lineno-1])):
                                lines[to_lineno-1] = lines[to_lineno-1][to_colno:]
                            del lines[to_lineno-1]
                            #Delete mid lines
                            for index in reversed(range(lineno, to_lineno-1)):
                                del lines[index]
                    else:
                        if(from_colno < to_colno):
                            from_colno, to_colno = to_colno, from_colno
                        if(lineinfo['source'] == 'UndoEvent'):
                            from_colno += 1
                        if(to_colno == -1):
                            lines[lineno-2] = lines[lineno-2] + lines[lineno-1]
                            del lines[lineno-1]
                        else:
                            if(to_lineno < len(lines) and lines[to_lineno-1][to_colno:from_colno] == ' ' and to_colno + 1 == len(lines[to_lineno-1])):
                                lines[to_lineno-1] = lines[to_lineno-1][:from_colno-1] + lines[to_lineno]
                                del lines[to_lineno]
                            else:
                                lines[lineno-1] = lines[lineno-1][:to_colno] + lines[lineno-1][from_colno:]
                    
    snapshot = "\n".join(lines)
    snapshot = snapshot.replace("\\n", r"\n")
    return snapshot

def countnodes(tree):
    ifcount, whilecount, forcount, assigncount, funcdefcount = 0, 0, 0, 0, 0
    for key, value in vars(tree).items():
        if(isinstance(value, list)):
            for listValue in value:
                if(isinstance(listValue, ast.If)):
                    ifcount += 1
                elif(isinstance(listValue, ast.While)):
                   whilecount += 1
                elif(isinstance(listValue, ast.For)):
                   forcount += 1
                elif(isinstance(listValue, ast.Assign) or isinstance(listValue, ast.AugAssign)):
                   assigncount += 1
                elif(isinstance(listValue, ast.FunctionDef)):
                   funcdefcount += 1
                addifcount, addwhilecount, addforcount, addassigncount, addfuncdefcount = countnodes(listValue)
                ifcount += addifcount
                whilecount += addwhilecount
                forcount += addforcount
                assigncount += addassigncount
                funcdefcount += addfuncdefcount
    return ifcount, whilecount, forcount, assigncount, funcdefcount

def getstats(logfilename):
    editors = geteditorids(logfilename)
    filenames = {}
    typeamt = 0
    pasteamt = 0
    runamt = 0
    erramt = 0
    synerramt = 0
    starttime = None
    endtime = None
    losefocusamt = 0
    stats = [["Time"]]
    runstats = [["Time"]]
    currenteditor = 0
    #Get file names, match them with editor ids
    with open("../user_logs/" + str(logfilename)) as logfile:
        for line in logfile:
            lineinfo = getlineinfo(line)
            if(line[0:4] == 'Load' or line[0:6] == 'SaveAs'): 
                if(lineinfo['editor_id'] not in filenames):
                    filenames[lineinfo['editor_id']] = lineinfo['filename'].split(r"\\")[-1].split("/")[-1]
            if(len(filenames) == len(editors)):
                break
            if(starttime == None):
                starttime = lineinfo['time']
                lasttime = lineinfo['time']
            
    if(len(editors) > len(filenames)):
        for editor in editors:
            if(editor not in filenames):
                filenames[str(editor)] = 'untitled'
    #Initialize stats and runstats lists
    for editor in editors:
        stats[0].append(filenames[str(editor)])
        runstats[0] = ["Time", "If", "While", "For", "Assign", "Function definitions"]
    #Get code additions per editor/file
    with open("../user_logs/" + str(logfilename)) as logfile:    
        for line in logfile:
            lineinfo = getlineinfo(line)
            endtime = lineinfo['time']
            if(line[0:10] == "TextInsert"):
                if(lineinfo['tags'] == 'None'):
                    if(lineinfo['editor_id'] in editors):
                        if(lineinfo['source'] == 'PasteEvent'):
                            pasteamt += len(lineinfo['text'])
                        elif(lineinfo['source'] == 'KeyPressEvent'):
                            typeamt += len(lineinfo['text'])
                        #Generate addition
                        addition = [str(endtime)[:-7]]
                        for i in range(1,len(editors)+1):
                            if(len(stats)>1):
                                addition.append(stats[-1][i])
                            else:
                                addition.append(0)
                        if(len(stats) > 1):
                            if(endtime - lasttime < timedelta(minutes=1)):
                                stats[-1][editors.index(lineinfo['editor_id'])+1] = stats[-1][editors.index(lineinfo['editor_id'])+1] + len(lineinfo['text'])
                            else:
                                addition[editors.index(lineinfo['editor_id'])+1] = stats[-1][editors.index(lineinfo['editor_id'])+1] + len(lineinfo['text'])
                                stats.append(addition)
                                lasttime = endtime
                        else:
                            addition[editors.index(lineinfo['editor_id'])+1] = len(lineinfo['text'])
                            stats.append(addition)
                            lasttime = endtime
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
                        pass
                        #from_colno = int(lineinfo['from_position'].split(".")[1])
                        #to_colno = int(lineinfo['to_position'].split(".")[1])
                        #deletion[editors.index(lineinfo['editor_id'])+1] = stats[-1][editors.index(lineinfo['editor_id'])+1] - (from_colno-to_colno)
                        #stats.append(deletion)
            elif(lineinfo['class'] == 'EditorLoseFocus'):
                losefocusamt += 1
            elif(lineinfo['class'] == 'Command' and (lineinfo['cmd_id'] == 'run_current_script' or lineinfo['cmd_id'] == 'debug_current_script')):
                runamt += 1
                #Generate addition
                addition = [""]
                for i in range(1, 5+1):
                        addition.append(0)
                try:
                    try:
                        ifcount, whilecount, forcount, assigncount, funcdefcount = countnodes(ast.parse(getsnapshot(currenteditor, lineinfo['time'], logfilename)))
                        addition[1], addition[2], addition[3], addition[4], addition[5] = ifcount, whilecount, forcount, assigncount, funcdefcount
                    except:
                        synerramt += 1
                except ValueError:
                    pass
                addition[0] = str(filenames[currenteditor])+ " \n" + str(lineinfo['time'])[:-7]
                runstats.append(addition)
            elif(lineinfo['class'] == 'EditorGetFocus'):
                currenteditor = lineinfo['editor_id']
        overalltime = endtime - starttime
        evendiff = overalltime/(len(stats)-1)
               
    erramt = erramt + (synerramt - erramt)
    return stats, runstats, pasteamt, typeamt, losefocusamt, runamt, erramt, starttime, endtime


def geteditorids(logfilename):
    editors = []
    with open("../user_logs/" + str(logfilename)) as logfile:
       for line in logfile:
           lineinfo = getlineinfo(line)
           if('editor_id' in lineinfo and lineinfo['editor_id'] not in editors and lineinfo['class'] != 'ShellCreate'):
                if('tags' in lineinfo):
                    if(lineinfo['tags'] == 'None'):
                        editors.append(lineinfo['editor_id'])
                #else:
                    #editors.append(lineinfo['editor_id']) 
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
      google.setOnLoadCallback(drawChart3);
      function drawChart() {
        var data = google.visualization.arrayToDataTable(
		"""+ str(stats) +""");
        var options = {
          title: 'Code additions in length over time'
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

       function drawChart3() {
        var data = google.visualization.arrayToDataTable(

        """ + str(runstats) + """

        );

        var options = {
          title: 'Ammount of nodes per run',
          hAxis: {title: 'Run time', titleTextStyle: {color: 'red'}}
        };

        var chart = new google.visualization.LineChart(document.getElementById('Column_chart'));
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
	<TD class=key> Number of unsuccessful runs: </TD>
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
        <div id="Column_chart" class=chart></div>
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

logfilename = "../user_logs/2014-04-22_19-47-54_0.txt"
logfiles = listdir("../user_logs")
statfiles = listdir("./")

for Logfilename in logfiles:
    editors = geteditorids(Logfilename)

    if (str(Logfilename[:-4])+".html" not in statfiles):
        stats, runstats, pasteamt, typeamt, losefocusamt, runamt, erramt, startdate, enddate = getstats("../user_logs/" + Logfilename)
        generatehtml(stats, pasteamt, typeamt, losefocusamt, runamt, erramt, startdate, enddate, Logfilename)

generateindex(logfiles)

