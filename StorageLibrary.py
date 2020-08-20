import sqlite3 as sl
import json

class StorageLibrary:
    global cur
    cur = None
    global maxValueDates
    maxValueDates = 3;
    
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
        

    def store(self,variableName,testSet,testId,data):
            # Note here will need to check the maximums allowed for "variableName+testSet+testId" to prevent flooding  without changing index
            global cur
            
            serializedData = json.dumps(data, sort_keys=True, indent=4)
            query = "INSERT INTO REMOTEDATA(testDate,variableName,testSet,testId,Content) \
                    VALUES(strftime('%s','now'),?,?,?,?);"
            args = (variableName,testSet,testId,serializedData)            
            try:
                cur.execute(query,args)
                cur.connection.commit()
            except sl.IntegrityError:
                raise Exception("Record with the given parameters ("+variableName+","+testSet+","+testId+") already exists in storage")
            count = self.retrieveCount(variableName,testSet,testId);
            if (count > maxValueDates):
                    self.RemoveXLatest(variableName,testSet,testId,count-maxValueDates)

    def RemoveXLatest(self,variableName,testSet,testId,count):
            query = "DELETE FROM REMOTEDATA WHERE id in (SELECT id FROM REMOTEDATA WHERE variableName = ? AND testSet = ? AND testId = ? ORDER BY testDate ASC LIMIT ?);"
            args = (variableName,testSet,testId,count)
            cur.execute(query,args)
            cur.connection.commit()


    def retrieveCount(self,variableName,testSet,testId):
            global cur
            query = "SELECT count(*) FROM REMOTEDATA WHERE variableName = ? AND testSet = ? AND testId = ?"
            args = (variableName,testSet,testId)
            cur.execute(query,args)
            counts = cur.fetchone()
            return(counts[0])

            
    def retrieveLatest(self,variableName,testSet=None,testId=None):
            global cur
            args = None
            query = None
            if variableName is None:
                raise Exception("Variable name was missing, it is a mandatory argument")
            if testSet is not None and testId is not None:
                query = "SELECT content FROM REMOTEDATA WHERE variableName = ? AND testSet = ? AND testId = ? AND testDate = (SELECT MAX(testDate) FROM REMOTEDATA)"
                args = (variableName,testSet,testId)
                cur.execute(query,args)
            if testSet is None and testId is None:
                query = "SELECT content FROM REMOTEDATA WHERE variableName = ? AND testDate = (SELECT MAX(testDate) FROM REMOTEDATA)"
                args = (variableName)
                cur.execute(query,[args])
            if testSet is None and testId is not None:
                query = "SELECT content FROM REMOTEDATA WHERE variableName = ? AND testId = ? AND testDate = (SELECT MAX(testDate) FROM REMOTEDATA)"
                args = (variableName,testId)
                cur.execute(query,args)
            if testSet is not None and testId is None:
                query = "SELECT content FROM REMOTEDATA WHERE variableName = ? AND testSet = ? AND testDate = (SELECT MAX(testDate) FROM REMOTEDATA)"
                args = (variableName,testSet)
                cur.execute(query,args)
            rows = cur.fetchall()
            data = json.loads(rows[0][0])
            return(data)

    def retrieveLatestAfter(self,variableName,testSet,testId,timestamp):
            global cur
            query = "SELECT content FROM REMOTEDATA WHERE variableName = ? AND testSet = ? AND testId = ? AND testDate > ?"
            args = (variableName,testSet,testId,timestamp)
            cur.execute(query,args)
            rows = cur.fetchall()
            data = json.loads(rows[0][0])
            return(data)

    def retrieveLatestBefore(self,variableName,testSet,testId,timestamp):
            global cur
            query = "SELECT content FROM REMOTEDATA WHERE variableName = ? AND testSet = ? AND testId = ? AND testDate testDate = (SELECT MAX(testDate) FROM REMOTEDATA WHERE testDate < ?)"
            args = (variableName,testSet,testId,timestamp)
            cur.execute(query,args)
            rows = cur.fetchall()
            data = json.loads(rows[0][0])
            return(data)

