from datetime import datetime, timedelta

def getlineinfo(line):
    linedict = {}
    timestamp = line[-27:-1]
    timestamp = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f")
    eventclass = line[0:10]
    linelist = line[11:-32].split(",",4)
    for pair in linelist:
        if(pair.split("=",1)[0][0] == " "):
            linedict[pair.split("=",1)[0][1:]] = pair.split("=",1)[1][1:-1]
        else:
            linedict[pair.split("=",1)[0]] = pair.split("=",1)[1][1:-1]
    linedict['class'] = eventclass
    linedict['time'] = timestamp
    return linedict

def getsnapshot(editor, time, filename):
    snapshot = ""
    lines = []
    sourceline = ""
    with open(filename) as logfile:
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
                    colno = int(lineinfo['position'].split(".")[1])
                    lineinfo['text'] = lineinfo['text'].replace(r"\t", " ")
                    if(lineno > len(lines)):
                        lines.append(lineinfo['text'].replace(r"\n", ""))
                        if(r"\n" in lineinfo['text']):
                            lines.append("")
                    else:
                        if(lineinfo['source'] == 'PasteEvent'):
                            lines[lineno-1] = lines[lineno-1][:colno-1] + lineinfo['text'] + lines[lineno-1][colno-1:]
                            insertedlines = lines[lineno-1].split(r"\n")
                            insertedlines.reverse()
                            for insertedline in insertedlines[:-1]:
                                   lines.insert(lineno, insertedline)
                            lines[lineno-1] = lines[lineno-1].split(r"\n")[0]
                        else:
                            lines[lineno-1] = lines[lineno-1][:colno-1] + lineinfo['text'] + lines[lineno-1][colno-1:]
                            if(r"\n" in lines[lineno-1]):
                                lines.insert(lineno, lines[lineno-1].split(r"\n")[1])
                                lines[lineno-1] = lines[lineno-1].split(r"\n")[0]
                                      
            elif(line[0:10] == "TextDelete"):
                lineinfo = getlineinfo(line)
                if (lineinfo['editor_id'] == editor and lineinfo['time']< time and lineinfo['source'] != 'LoadEvent'):
                    lineno = int(lineinfo['from_position'].split(".")[0])
                    from_colno = int(lineinfo['from_position'].split(".")[1])
                    to_colno = int(lineinfo['to_position'].split(".")[1])
                    if(lineinfo['source'] == 'UndoEvent' or lineinfo['source'] == 'RedoEvent'):
                        from_colno += 1
                    if(to_colno == -1):
                        lines[lineno-2] = lines[lineno-2] + lines[lineno-1][from_colno:]
                        del lines[lineno-1]
                    else:
                        lines[lineno-1] = lines[lineno-1][:to_colno] + lines[lineno-1][from_colno:]
            print(lines)
                    
    snapshot = "\n".join(lines)
    snapshot = snapshot.replace(r"\n", "\n")
    return snapshot

Filename = "examplelog.txt"
editor = str(46381712)
time = timedelta(minutes = 5)

snapshot = getsnapshot(editor, time, Filename)
print (snapshot)
