import sqlite3 as sl
import json
import time
from datetime import datetime
from datetime import timezone


class StorageLibrary:
    """(Remote)storagelibrary is for storing variable values using robotframework remote library interface. Can be used for connecting separate test suites or runs by different teams.
    
    Note that although StorageLibrary can be used locally, and you could import it directly as StorageLibrary.py it is not intended for such usage. Instead it should be runnin separately as a remote library.
    """
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'
    ROBOT_SUPPRESS_NAME = True
    ROBOT_AUTO_KEYWORDS = False

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
            PRAGMA encoding = 'UTF-8'; 
            ''')
            
            cur.execute('''
                CREATE TABLE REMOTEDATA (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    variableName TEXT,
                    environment TEXT,
                    testSet TEXT,
                    testId TEXT,
                    testDate REAL,
                    Content TEXT,
                    UNIQUE(variableName,testSet,testId,testDate)
                );
            ''')
            print("Creating indexes")
            cur.execute('''CREATE INDEX variableName_idx ON REMOTEDATA(variableName);''')
            cur.execute('''CREATE INDEX environment_idx ON REMOTEDATA(environment);''')
            cur.execute('''CREATE INDEX testSet_idx ON REMOTEDATA(testSet);''')
            cur.execute('''CREATE INDEX testId_idx ON REMOTEDATA(testId);''')
            cur.execute('''CREATE INDEX testDate_idx ON REMOTEDATA(testDate);''')
            
            cur.connection.commit()
            print("Database created")
        else:
            print("Connected to existing database")
        

    def store(self,variable_name,data,environment=None,test_set=None,test_id=None):
            """Stores the given variable to a SQLITE database as a json serialized string. 
            
            The variable values are stored with timestamps. 
            At most 365 versions are retained for same combination of variable_name,environment,test_set and test_id.
            When more than 356 versions are stored the oldest value is removed from storage.
            
            Arguments:
            
            variable_name:  name to use when storing the variable (mandatory)
            
            data:  either a String, Integer, Number, List or Dictionary. (mandatory)
            
            environment:  name of the test environment (optional)
            
            test_set:  name of the test set, e.g. "E2E tests" (optional)
            
            test_id:  name of the test, e.g. "E2E test1" (optional)
            

            Examples:
            
            Set Remote Variable  |  InventedVariableName  |  ${My variable} 
            
            Set Remote Variable  |  data=${My variable} | variable_name=My variable Name  | environment=TEST
            
            Set Remote Variable  |  variable_name=My variable Name  |  environment=TEST  | test_set=E2E  | test_id=E2E test 1  | data=${My variable}
            

            The variable values are stored with timestamps. At most 365 versions are retained for same combination of variable_name,environment,test_set and test_id, when more than 356 versions are stored the oldest value is removed.
            """
            # Note here will need to check the maximums allowed for "variableName+testSet+testId" to prevent flooding - e.g. by test reruns
            global cur
            if variable_name is None:
                raise Exception("Variable name was missing, it is a mandatory argument")
            environment_name = environment
            testSet = test_set
            testId = test_id
            if testSet is None:
                testSet = ""
            if testId is None:
                testId = ""
            if environment_name is None:
                environment_name = ""
            serializedData = json.dumps(data, sort_keys=True, indent=4)            
            query = "INSERT INTO REMOTEDATA(testDate,variableName,environment,testSet,testId,Content) \
                    VALUES(?,?,?,?,?,?);"
            args = (datetime.now(timezone.utc).timestamp(),variable_name,environment_name,testSet,testId,serializedData)            
            try:
                cur.execute(query,args)
                cur.connection.commit()
            except sl.IntegrityError:
                time.sleep(0.05)
                query = "INSERT INTO REMOTEDATA(testDate,variableName,environment,testSet,testId,Content) \
                        VALUES(?,?,?,?,?,?);"
                args = (datetime.now(timezone.utc).timestamp(),variable_name,environment_name,testSet,testId,serializedData)            
                try:
                    cur.execute(query,args)
                    cur.connection.commit()
                except sl.IntegrityError:
                    raise Exception("Record with the given parameters ("+str(variable_name)+","+str(environment_name)+","+str(testSet)+","+str(testId)+") already exists in storage for current timestamp")
                
            count = self.retrieve_count(variable_name,environment,testSet,testId);
            if (count > maxValueDates):
                    self.remove_X_Latest(variableName,testSet,testId,count-maxValueDates)

    def remove_X_Latest(self,variableName,environment,testSet,testId,count):
            query = "DELETE FROM REMOTEDATA WHERE id in (SELECT id FROM REMOTEDATA WHERE variableName = ? AND environment= ? AND testSet = ? AND testId = ? ORDER BY testDate ASC LIMIT ?);"
            args = (variableName,environment,testSet,testId,count)
            cur.execute(query,args)
            cur.connection.commit()

    def retrieve_count(self,variableName,environment,testSet,testId):
            global cur
            query = "SELECT count(*) FROM REMOTEDATA WHERE variableName = ? AND environment = ? AND testSet = ? AND testId = ?"
            args = (variableName,environment,testSet,testId)
            cur.execute(query,args)
            counts = cur.fetchone()
            return(counts[0])

    def retrieve_latest(self,variable_name,environment=None,test_set=None,test_id=None,after=None,before=None,fail_if_not_found=False):
            global cur
            if variable_name is None:
                raise Exception("Variable name was missing, it is a mandatory argument")

            # query based on variableName and optional environment, testSet and testId
            args = [variable_name]
            query = "SELECT Content FROM REMOTEDATA WHERE variableName = ? "
            if environment is not None:
                query = query + "AND environment = ? "
                args.append(environment)
            if test_set is not None:
                query = query + "AND testSet = ? "
                args.append(test_set)
            if test_id is not None:
                query = query + "AND testId = ? "
                args.append(test_id)
            
            # date range to use
            query = query + "AND testDate = (SELECT MAX(testDate) FROM REMOTEDATA  WHERE variableName = ? "
            args.append(variable_name)
            if after is not None:
                query = query + "AND testDate > ? "
                args.append(after)
            if before is not None:
                query = query + "AND testDate < ? "
                args.append(before)
            # add the where conditions to the date select
            if environment is not None:
                query = query + "AND environment = ? "
                args.append(environment)
            if test_set is not None:
                query = query + "AND testSet = ? "
                args.append(test_set)
            if test_id is not None:
                query = query + "AND testId = ? "
                args.append(test_id)
                
            query = query + ");"            
            cur.execute(query,tuple(args))
            rows = cur.fetchall()
            try:
                if len(rows) > 1:
                    data = json.loads(rows[len(rows)-1][0])
                else:
                    data = json.loads(rows[0][0])
            except IndexError: 
                if (fail_if_not_found):
                    raise Exception("Variable with the given parameters was not found")
                else:
                    return None                
            return(data)

    retrieve_latest.robot_name = "Get Remote Variable"
    store.robot_name = "Set Remote Variable"
