*** Settings ***
Documentation     Self tests for the remote storage library
...

Library           Remote  http://127.0.0.1:8270
Library           DateTime

*** Test Cases ***

Set and get Strings
    Set Remote Variable   myvar   data=blaad2   test_set=myset2
    Set Remote Variable   myvar   data=blaad   environment=myenv   test_set=myset   test_id=myid
    Set Remote Variable   myvarEmpty   data=${EMPTY}   environment=myenv   test_set=myset   test_id=myid
    ${UTFChar}=    Evaluate   '\u30b8' 
    Set Remote Variable   myvarUTF   data=${UTFChar}   environment=myenv   test_set=myset   test_id=myid
    
    ${var}=  Get Remote Variable   myvar
    Should be Equal  ${var}  blaad
    ${var}=  Get Remote Variable   myvar   environment=myenv
    Should be Equal  ${var}  blaad
    ${var}=  Get Remote Variable   myvar   environment=myenv
    Should be Equal  ${var}  blaad
    ${var}=  Get Remote Variable   myvar   test_set=myset2
    Should be Equal  ${var}  blaad2
    ${var}=  Get Remote Variable   myvarEmpty   test_set=myset
    Should be Equal  ${var}  ${EMPTY}
    ${var}=  Get Remote Variable   myvarUTF   test_set=myset
    Should be Equal  ${var}  ${UTFChar}



Set and get Integer
    ${MyInteger}=    Convert To Integer    123
    Set Remote Variable   myvar   data=${MyInteger}   test_set=myset2
    ${var}=  Get Remote Variable   myvar
    Should be Equal  ${var}  ${MyInteger}

Set and Get Float
    ${MyFloat}=    Convert To Number    123.123
    Set Remote Variable   myvar   data=${MyFloat}   test_set=myset2
    ${var}=  Get Remote Variable   myvar
    Should be Equal  ${var}  ${MyFloat}


Set and get List
    @{MyList}=    Create List    item1    item2    item3
    Set Remote Variable   myvar   data=${MyList}   test_set=myset2
    ${var}=  Get Remote Variable   myvar
    Should be Equal  ${var}  ${MyList}

    
Set and get Dictionary
    &{MyDict} = 	Create Dictionary 	key=value 	foo=bar 		
    Set Remote Variable   myvar   data=${MyDict}   test_set=myset2
    ${var}=  Get Remote Variable   myvar
    Should be Equal  ${var}  ${MyDict}

Set and get using timestamp
    ${timestamp1}=   Get Current Date   result_format=epoch
    Set Remote Variable   myvarTimestamp   data=timetest1  environment=myenv   test_set=myset   test_id=myid
    ${timestamp2}=   Get Current Date   result_format=epoch
    Set Remote Variable   myvarTimestamp   data=timetest2  environment=myenv   test_set=myset   test_id=myid    
    ${timestamp3}=   Get Current Date   result_format=epoch
    Set Remote Variable   myvarTimestamp   data=timetest3  environment=myenv   test_set=myset   test_id=myid
    ${timestamp4}=   Get Current Date   result_format=epoch
    
    Comment  Getting without time arguments should return latest value    
    ${var}=  Get Remote Variable   myvarTimestamp
    Should be Equal  ${var}  timetest3

    Comment  Getting with 'before' time argument should return latest value before given timestamp    
    ${var}=  Get Remote Variable   myvarTimestamp   before=${timestamp3}
    Should be Equal  ${var}  timetest2
    
    Comment  Getting with 'after' time argument should return latest value after given timestamp        
    ${var}=  Get Remote Variable   myvarTimestamp   after=${timestamp2}
    Should be Equal  ${var}  timetest3

    Comment  Getting with 'before' argument in future should return latest value
    ${var}=  Get Remote Variable   myvarTimestamp   before=${timestamp4}
    Should be Equal  ${var}  timetest3
    
    Comment  Getting with 'after' argument in future should return empty value
    ${var}=  Get Remote Variable   myvarTimestamp   after=${timestamp4}
    Should be Equal  ${var}  ${EMPTY}
    
    Comment  Getting with 'before' and 'after' arguments should return latest value in the time range
    ${var}=  Get Remote Variable   myvarTimestamp   after=${timestamp2}  before=${timestamp3}
    Should be Equal  ${var}  timetest2
    ${var}=  Get Remote Variable   myvarTimestamp   after=${timestamp3}  before=${timestamp4}
    Should be Equal  ${var}  timetest3
    ${var}=  Get Remote Variable   myvarTimestamp   after=${timestamp1}  before=${timestamp4}
    Should be Equal  ${var}  timetest3
