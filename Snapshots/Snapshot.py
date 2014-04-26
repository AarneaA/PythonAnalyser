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
                    if(lineinfo['text'] == r"\n"):
                        colno -= 1
                    lineinfo['text'] = lineinfo['text'].replace(r"\t", " ")
                    lineinfo['text'] = lineinfo['text'].replace(r"\n", r" \n")
                    if(lineno > len(lines)):
                        lines.append(lineinfo['text'].replace(r"\n", ""))
                        """
                        if(r"\n" in lineinfo['text']):
                            lines[-1] = lines[-1] + ""
                            print("Appending")
                            lines.append("asd")
                        """
                    else:
                        if(lineinfo['source'] == 'PasteEvent' or lineinfo['source'] == 'RedoEvent' or lineinfo['source'] == 'UndoEvent'):
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
                    to_lineno = int(lineinfo['to_position'].split(".")[0])
                    from_colno = int(lineinfo['from_position'].split(".")[1])
                    to_colno = int(lineinfo['to_position'].split(".")[1])
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
                            if(lineno < len(lines) and lines[lineno-1][to_colno:from_colno+1] == ' ' and from_colno == len(lines[lineno-1])):
                                lines[lineno-2] = lines[lineno-1][:to_colno] + lines[lineno-1][from_colno:]
                                lines[lineno-2] = lines[lineno-1] + lines[lineno]
                                del lines[lineno-1]
                            else:
                                lines[lineno-1] = lines[lineno-1][:to_colno] + lines[lineno-1][from_colno:]
                    
    snapshot = "\n".join(lines)
    snapshot = snapshot.replace(r"\n", "\n")
    return snapshot

Filename = "examplelog.txt"
editor = str(46381712)
time = datetime.now()

snapshot = getsnapshot(editor, time, Filename)
print (snapshot)
