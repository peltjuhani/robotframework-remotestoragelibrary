import sqlite3 as sl
import json
import time
from datetime import datetime
from datetime import timezone


class StorageLibrary:
    """(Remote)Storage library is for storing variable values using robotframework remote library interface. It can be used e.g. for connecting separate test suites or runs by different teams.

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
                    identifierName TEXT,
                    dataDate REAL,
                    Content TEXT,
                    UNIQUE(variableName,identifierName,dataDate)
                );
            ''')
            print("Creating indexes")
            cur.execute('''CREATE INDEX variableName_idx ON REMOTEDATA(variableName);''')
            cur.execute('''CREATE INDEX identifier_idx ON REMOTEDATA(identifierName);''')
            cur.execute('''CREATE INDEX dataDate_idx ON REMOTEDATA(dataDate);''')
            
            cur.connection.commit()
            print("Database created")
        else:
            print("Connected to existing database")
        

    def store(self,variable_name,data,identifier_name=None):
            """Stores the given variable to a SQLITE database as a json serialized string. 
            
            The variable values are stored with timestamps. 
            At most 365 versions are retained for same combination of variable_name and (optional) identifier.
            When more than 356 versions are stored the oldest value is removed from storage.
            
            Arguments:
            
            variable_name:  name to use when storing the variable (mandatory)
            
            identifier_name:  additional identifier, e.g. environment name (optional)                        

            data:  either a String, Integer, Number, List or Dictionary. (mandatory)
            
            Examples:
            
            Set Stored Variable  |  InventedVariableName  |  ${My variable} 
            
            Set Stored Variable  |  data=${My variable} | variable_name=My variable Name  | identifier_name=TST_ENV
                        

            The variable values are stored with timestamps. At most 365 versions are retained for same combination of variable_name and identifier_name. When more than 356 versions are stored the oldest value is removed.
            """
            global cur
            if variable_name is None:
                raise Exception("Variable name was missing, it is a mandatory argument")
            if not identifier_name:
                identifier_name = ""
            serializedData = json.dumps(data, sort_keys=True, indent=4)            
            query = "INSERT INTO REMOTEDATA(dataDate,variableName,identifierName,Content) \
                    VALUES(?,?,?,?);"
            args = (datetime.now(timezone.utc).timestamp(),variable_name,identifier_name,serializedData)            
            try:
                cur.execute(query,args)
                cur.connection.commit()
            except sl.IntegrityError:
                time.sleep(0.05)
                query = "INSERT INTO REMOTEDATA(dataDate,variableName,identifierName,Content) \
                        VALUES(?,?,?,?);"
                args = (datetime.now(timezone.utc).timestamp(),variable_name,identifier_name,serializedData)            
                try:
                    cur.execute(query,args)
                    cur.connection.commit()
                except sl.IntegrityError:
                    raise Exception("Record with the given parameters ("+str(variable_name)+","+str(identifier_name)+") already exists in storage for current timestamp")
                
            count = self.retrieve_count(variable_name,identifier_name);
            if (count > maxValueDates):
                    self.remove_X_Latest(variable_name,identifier_name,count-maxValueDates)

    def remove_X_Latest(self,variable_name,identifier_name,count):
            query = "DELETE FROM REMOTEDATA WHERE id in (SELECT id FROM REMOTEDATA WHERE variableName = ? AND identifierName= ? ORDER BY dataDate ASC LIMIT ?);"
            args = (variable_name,identifier_name,count)
            cur.execute(query,args)
            cur.connection.commit()

    def retrieve_count(self,variable_name,identifier_name):
            global cur
            query = "SELECT count(*) FROM REMOTEDATA WHERE variableName = ? AND identifierName = ?"
            args = (variable_name,identifier_name)
            cur.execute(query,args)
            counts = cur.fetchone()
            return(counts[0])

    def storagetimestamp(self):
            """Utility function to retrieve the current timestamp in the storage server"""
            return(datetime.now(timezone.utc).timestamp())

    def retrieve_latest(self,variable_name,identifier_name=None,after=None,before=None,fail_if_not_found=False):
            """Retrieves the given variable from remote storage and returns it as a robot framework variable. 
                        
            Arguments:
            
            variable_name:  name to use when storing the variable (mandatory)
                        
            identifier_name:  additional identifier, e.g. environment name (optional)
            
            before:   Epoch timestamp at or before which the variable was stored (including the given timestamp)
            
            after:    Epoch timestamp at or after which the variable was stored (including the given timestamp)
            
            fail_if_not_found: defaults to ${False}, and then returns $[EMPTY} if variable is not found. If ${True} is given then will FAIL the keyword instead.
            
            NOTE: The timestamp is the epoch timestamp returned with "${timestamp}=   Get Current Date   result_format=epoch"
            
            ( "Get Current Date" keyword is defined in Robot Framework DateTime standard library. )

            Examples:
            
            ${TheVariableName} =  |  Get Stored Variable  |  TheVariableName
            
            -- This retrieves the latest stored variable with name TheVariableName regardless of additional identifier values
            
            ${TheVariableName} =  |  Get Stored Variable  |  TheVariableName | fail_if_not_found=${True}
            
            -- This retrieves the latest stored variable with name TheVariableName regardless of additional identifier values. If no variable is found then the keyword will fail

            ${TheVariableName} =  |  Get Stored Variable  |  TheVariableName | identifier_name=DEV_ENV
            
            -- This retrieves the latest stored variable with name TheVariableName having additional identifier "DEV_ENV"
            
            ${dayAgo}=  |  Get Current Date |  increment=-1 day  |  result_format=epoch
            
            ${myVar} =  |  Get Stored Variable  |  TheVariableName | identifier_name=E2E test 1 | before=${dayAgo}
            
            -- This retrieves the latest stored variable with name TheVariableName and additional identifier "E2E test 1" that was stored at least one day ago.
            
            ${dayAgo}=  |  Get Current Date |  increment=-1 day  |  result_format=epoch
            
            ${weekAgo}=  |  Get Current Date |  increment=-7 days  |  result_format=epoch
            
            ${myVar} =  |  Get Stored Variable  |  TheVariableName | identifier_name=E2E test 1 | before=${dayAgo} | after=${weekAgo}
            
            -- This retrieves the latest stored variable with name TheVariableName and additional identifier "E2E test 1" that was stored between 1 and 7 days ago
            
            
            """    
            global cur
            if variable_name is None:
                raise Exception("Variable name was missing, it is a mandatory argument")

            # query based on variableName and optional identifier
            args = [variable_name]
            query = "SELECT Content FROM REMOTEDATA WHERE variableName = ? "
            if identifier_name:
                print("Adding identifier")
                query = query + "AND identifierName = ? "
                args.append(identifier_name)
            
            # date range to use
            query = query + "AND dataDate = (SELECT MAX(dataDate) FROM REMOTEDATA  WHERE variableName = ? "
            args.append(variable_name)
            if after is not None:
                query = query + "AND dataDate >= ? "
                args.append(after)
            if before is not None:
                query = query + "AND dataDate <= ? "
                args.append(before)
            # add the where conditions to the date select
            if identifier_name:
                print("Adding identifier")
                query = query + "AND identifierName = ? "
                args.append(identifier_name)
                
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

    retrieve_latest.robot_name = "Get Stored Variable"
    store.robot_name = "Set Stored Variable"
    storagetimestamp.robot_name = "Get Storage Timestamp"
