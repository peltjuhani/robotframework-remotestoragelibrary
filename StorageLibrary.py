import sqlite3 as sl
import json
import time
from datetime import datetime
from datetime import timezone


class StorageLibrary:
    """RemoteStorage library is for storing variable values using robotframework remote library interface. It can be used e.g. for connecting separate test suites or runs by different teams.

    Installing:
    First install robotremoteserver as described in (https://pypi.org/project/robotremoteserver/ ), e.g.:  pip install robotremoteserver
    
    Then install robotframework-remotestoragelibrary:  
    (at minimum download the robotframework-remotestoragelibrary.py and StorageLibrary.py)
    
    Running:
    python robotframework-remotestoragelibrary.py
    
    See also "python robotframework-remotestoragelibrary.py --help" for options on running.
    
    Importing:
    Library           Remote  http://<serverIPaddress>:8270
    
    Note that although the library could be imported locally as StorageLibrary.py the benefits come when running as a remote library.
    """
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'
    ROBOT_SUPPRESS_NAME = True
    ROBOT_AUTO_KEYWORDS = False
    ROBOT_LIBRARY_VERSION  = '0.1'

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
            """Retrieves the given variable from remote storage and returns it as a robot framework variable. 
                        
            Arguments:
            
            variable_name:  name to use when storing the variable (mandatory)
                        
            environment:  name of the test environment (optional)
            
            test_set:  name of the test set, e.g. "E2E tests" (optional)
            
            test_id:  name of the test, e.g. "E2E test1" (optional)
            
            before:  the timestamp before the variable was stored (optional)
            
            after:  the timestamp after the variable was stored (optional)
            
            fail_if_not_found: defaults to ${False}, and then returns $[EMPTY} if variable is not found. If ${True} is given then will FAIL the keyword instead.
            
            before:    Epoch timestamp before which the variable was stored
            
            after:    Epoch timestamp after which the variable was stored
            
                                            
            NOTE: The timestamp is the epoch timestamp returned with "${timestamp}=   Get Current Date   result_format=epoch"
            
            ( "Get Current Date" keyword is defined in Robot Framework DateTime standard library. )


            Examples:
            
            ${myVar} =  |  Get Remote Variable  |  TheVariableName
            
            -- This retrieves the latest stored variable with name TheVariableName for any environment, testset etc. values
            
            ${myVar} =  |  Get Remote Variable  |  TheVariableName | fail_if_not_found=${True}
            
            -- This retrieves the latest stored variable with name TheVariableName for any environment, testset etc. values. If no variable is found then the keyword will fail

            ${myVar} =  |  Get Remote Variable  |  TheVariableName | environment=TEST  | test_set=E2E  | test_id=E2E test 1 
            
            -- This retrieves the latest stored variable with name TheVariableName for "TEST" environment and test set "E2E", and test id "E2E test 1" 
            
            ${dayAgo}=  |  Get Current Date |  increment=-1 day  |  result_format=epoch
            
            ${myVar} =  |  Get Remote Variable  |  TheVariableName | test_id=E2E test 1 | before=${dayAgo}
            
            -- This retrieves the latest stored variable with name TheVariableName and test id "E2E test 1" that was stored at least one day ago.
            
            ${dayAgo}=  |  Get Current Date |  increment=-1 day  |  result_format=epoch
            
            ${weekAgo}=  |  Get Current Date |  increment=-7 days  |  result_format=epoch
            
            ${myVar} =  |  Get Remote Variable  |  TheVariableName | test_id=E2E test 1 | before=${dayAgo} | after=${weekAgo}
            
            -- This retrieves the latest stored variable with name TheVariableName and test id "E2E test 1" that was stored between 1 and 7 days earlier
            
            
            """    
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
