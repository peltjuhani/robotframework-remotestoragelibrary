# robotframework-remotestoragelibrary
Remotestoragelibrary is for storing variable values using robotframework remote library interface. Used for connecting separate test suites or runs by different teams.

Basic idea:

Using a remotely running Robot Framework remote library to expose keywords that allow storing variable values (along with some metadata to identify test run etc) to that server where the remote library is running. The difference to using some existing e.g. REST api based storage is to make the usage extremely easy for Robot Framework users.