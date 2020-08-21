import sqlite3 as sl
import json

class StorageLibrary:
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'
    ROBOT_SUPPRESS_NAME = True

    global cur
    cur = None
    global maxValueDates
    maxValueDates = 365;
    
    def __init__(self):
        global cur
        # First create needed table(s) if they are missing
        con = sl.connect('remotestorage.db')
        cur = con.cursor()
        cur.execute('''SELECT * FROM sqlite_master WHERE type='table' AND name='REMOTEDATA';''')
        rows = cur.fetchall()
        if len(rows) == 0 :
            print("Creating new database")
            cur.execute('''
                CREATE TABLE REMOTEDATA (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    variableName TEXT,
                    testSet TEXT,
                    testId TEXT,
                    testDate INTEGER,
                    Content TEXT,
                    UNIQUE(variableName,testSet,testId,testDate)
                );
            ''')
            print("Creating indexes")
            cur.execute('''CREATE INDEX testSet_idx ON REMOTEDATA(testSet);''')
            cur.execute('''CREATE INDEX testId_idx ON REMOTEDATA(testId);''')
            cur.execute('''CREATE INDEX testDate_idx ON REMOTEDATA(testDate);''')
            print("Database created")
        else:
            print("Connected to existing database")
        #self.store("myvar","blaaad","myset","myid")
        #self.store("myvar","blaaad3")
        #print(self.retrieve_latest("myvar","myset","myid"))
        #print(self.retrieve_latest(testSet="myset",variableName="myvar"))
        #print(self.retrieve_latest("myvar"))
        

    def store(self,variableName,data,testSetIN=None,testIdIN=None):
            robot_name = 'store to remote'
            # Note here will need to check the maximums allowed for "variableName+testSet+testId" to prevent flooding - e.g. by test reruns
            global cur
            testSet = testSetIN
            if testSetIN is None:
                testSet = ""
            testId = testIdIN
            if testIdIN is None:
                testId = ""
                
            serializedData = json.dumps(data, sort_keys=True, indent=4)            
            
            query = "INSERT INTO REMOTEDATA(testDate,variableName,testSet,testId,Content) \
                    VALUES(strftime('%s','now'),?,?,?,?);"
            args = (variableName,testSet,testId,serializedData)            
            try:
                cur.execute(query,args)
                cur.connection.commit()
            except sl.IntegrityError:
                raise Exception("Record with the given parameters ("+variableName+","+testSet+","+testId+") already exists in storage for current timestamp")
            count = self.retrieve_count(variableName,testSet,testId);
            if (count > maxValueDates):
                    self.remove_X_Latest(variableName,testSet,testId,count-maxValueDates)

    def remove_X_Latest(self,variableName,testSet,testId,count):
            query = "DELETE FROM REMOTEDATA WHERE id in (SELECT id FROM REMOTEDATA WHERE variableName = ? AND testSet = ? AND testId = ? ORDER BY testDate ASC LIMIT ?);"
            args = (variableName,testSet,testId,count)
            cur.execute(query,args)
            cur.connection.commit()

    def retrieve_count(self,variableName,testSet,testId):
            global cur
            query = "SELECT count(*) FROM REMOTEDATA WHERE variableName = ? AND testSet = ? AND testId = ?"
            args = (variableName,testSet,testId)
            cur.execute(query,args)
            counts = cur.fetchone()
            return(counts[0])

    def retrieve_latest(self,variableName,testSet=None,testId=None,after=None,before=None):
            robot_name = 'get latest value for remote variable'
            global cur
            if variableName is None:
                raise Exception("Variable name was missing, it is a mandatory argument")

            # query based on variableName and optional testSet and testId
            args = [variableName]
            query = "SELECT content FROM REMOTEDATA WHERE variableName = ? "
            if testSet is not None:
                query = query + "AND testSet = ? "
                args.append(testSet)
            if testId is not None:
                query = query + "AND testId = ? "
                args.append(testId)
            
            # date range to use
            query = query + "AND testDate = (SELECT MAX(testDate) FROM REMOTEDATA WHERE 1=1 "             
            if after is not None:
                query = query + "testDate > ? "
                args.append(after)
            if after is not None and before is not None:
                query = query + "AND "
            if before is not None:
                query = query + "testDate < ? "
                args.append(before)
            # add the where conditions to the date select
            if testSet is not None:
                query = query + "AND testSet = ? "
                args.append(testSet)
            if testId is not None:
                query = query + "AND testId = ? "
                args.append(testId)
                
            query = query + ");"
            cur.execute(query,tuple(args))
            rows = cur.fetchall()
            data = json.loads(rows[0][0])
            return(data)
