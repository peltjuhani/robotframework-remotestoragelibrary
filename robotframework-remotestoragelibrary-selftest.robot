*** Settings ***
Documentation     Self tests for the remote storage library
...               Running the tests: 
...                   1 Install robot framework ( pip install robotframework )
...                   2 Start remotelibrary ( python robotframework-remotestoragelibrary.py )
...                   3 Run robot tests ( python -m robot robotframework-remotestoragelibrary-selftest.robot )

Library           Remote  http://127.0.0.1:8270
Library           DateTime
Library           OperatingSystem

*** Test Cases ***

Set and get Strings
    Set Stored Variable   myvar   data=blaad2   identifier_name=myset2
    Set Stored Variable   myvar   data=blaad   identifier_name=myenv
    Set Stored Variable   myvarEmpty   data=${EMPTY}   identifier_name=myenv
    ${UTFChar}=    Evaluate   '\u30b8' 
    Set Stored Variable   myvarUTF   data=${UTFChar}
    
    ${var}=  Get Stored Variable   myvar
    Should be Equal  ${var}  blaad
    ${var}=  Get Stored Variable   myvar   identifier_name=myenv
    Should be Equal  ${var}  blaad
    ${var}=  Get Stored Variable   myvar   identifier_name=myenv
    Should be Equal  ${var}  blaad
    ${var}=  Get Stored Variable   myvar   identifier_name=myset2
    Should be Equal  ${var}  blaad2
    ${var}=  Get Stored Variable   myvarEmpty   identifier_name=myenv
    Should be Equal  ${var}  ${EMPTY}
    ${var}=  Get Stored Variable   myvarUTF
    Should be Equal  ${var}  ${UTFChar}


Set and get Integer
    ${MyInteger}=    Convert To Integer    123
    Set Stored Variable   myvar   data=${MyInteger}   identifier_name=myset2
    ${var}=  Get Stored Variable   myvar
    Should be Equal  ${var}  ${MyInteger}

Set and Get Float
    ${MyFloat}=    Convert To Number    123.123
    Set Stored Variable   myvar   data=${MyFloat}   identifier_name=myset2
    ${var}=  Get Stored Variable   myvar
    Should be Equal  ${var}  ${MyFloat}


Set and get List
    @{MyList}=    Create List    item1    item2    item3
    Set Stored Variable   myvar   data=${MyList}   identifier_name=myset2
    ${var}=  Get Stored Variable   myvar
    Should be Equal  ${var}  ${MyList}

    
Set and get Dictionary
    &{MyDict} = 	Create Dictionary 	key=value 	foo=bar 		
    Set Stored Variable   myvar   data=${MyDict}   identifier_name=myset2
    ${var}=  Get Stored Variable   myvar
    Should be Equal  ${var}  ${MyDict}

Set and get using timestamp
    ${timestamp1}=   Get Current Date   result_format=epoch
    Set Stored Variable   myvarTimestamp   data=timetest1  identifier_name=myenv
    ${timestamp2}=   Get Current Date   result_format=epoch
    Set Stored Variable   myvarTimestamp   data=timetest2
    ${timestamp3}=   Get Current Date   result_format=epoch
    Sleep  0.01 s    # need to spleep a bit here, otherwise timetest2 and timetest3 timestamps might be same due to clock accuracy limitations
    Set Stored Variable   myvarTimestamp   data=timetest3  identifier_name=myenv
    ${timestamp4}=   Get Current Date   increment=1 s   result_format=epoch
    ${longAgo}=      Get Current Date   increment=-5700 days   result_format=epoch
    
    Comment  Getting without time arguments should return latest value    
    ${var}=  Get Stored Variable   myvarTimestamp
    Should be Equal  ${var}  timetest3

    Comment  Getting with 'before' time argument should return latest value before given timestamp    
    ${var}=  Get Stored Variable   myvarTimestamp   before=${timestamp3}
    Should be Equal  ${var}  timetest2
    
    Comment  Getting with 'after' time argument should return latest value after given timestamp
    ${var}=  Get Stored Variable   myvarTimestamp   after=${timestamp2}   identifier_name=myenv
    Should be Equal  ${var}  timetest3

    Comment  Getting with 'after' time argument without identifier should also return latest value after given timestamp
    ${var}=  Get Stored Variable   myvarTimestamp   after=${timestamp2}
    Should be Equal  ${var}  timetest3

    Comment  Getting with 'before' argument in future should return latest value
    ${var}=  Get Stored Variable   myvarTimestamp   before=${timestamp4}
    Should be Equal  ${var}  timetest3
    
    Comment  Getting with 'after' argument in future should return empty value
    ${var}=  Get Stored Variable   myvarTimestamp   after=${timestamp4}
    Should be Equal  ${var}  ${EMPTY}
    
    Comment  Getting with 'before' and 'after' arguments should return latest value in the time range
    ${var}=  Get Stored Variable   myvarTimestamp   after=${timestamp2}  before=${timestamp3}
    Should be Equal  ${var}  timetest2
    ${var}=  Get Stored Variable   myvarTimestamp   after=${timestamp3}  before=${timestamp4}
    Should be Equal  ${var}  timetest3
    ${var}=  Get Stored Variable   myvarTimestamp   after=${timestamp1}  before=${timestamp4}
    Should be Equal  ${var}  timetest3
    
    ${var}=  Get Stored Variable   myvarTimestamp   before=${longAgo}
    Should be Equal  ${var}  ${EMPTY}
    

Get non-existing
    # empty response bt default
    ${var}=  Get Stored Variable   myvarNoExist
    Should be Equal  ${var}  ${EMPTY}
    
    # failure if requested to fail on not found
    Run Keyword And Expect Error  	Variable with the given parameters was not found    Get Stored Variable   myvarNoExist   fail_if_not_found=${True}

