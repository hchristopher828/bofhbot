import json
import sqlite3
from pandas.io.json import json_normalize
import time
from time import gmtime, strftime
import sqlalchemy
import pandas as pd
import collections
import datetime

try:
    collectionsAbc = collections.abc
except AttributeError:
    collectionsAbc = collections


def db_storage(data, db_url):
    print(db_url)
    data2 = data
    def flatten(d, parent_key = "", sep = "_"):
        items = []
        for k, v in d.items():
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, collectionsAbc.MutableMapping):
                items.extend(flatten(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)   #Function to flatten the dictionary in the dictionary object
    for x in data2:
        data2[x] = flatten(data2[x])
    df = pd.DataFrame(data2).T  #Transpose the dataframe to get what we want
    df["USER_BOOL"] = ["None" if df["USER_PROCESSES"][i] is None else "Empty" if len(df["USER_PROCESSES"][i]) == 0 else "Yes"
for i in range(0,df.shape[0])]  #Add a boolean column to identify if there are "empty", "none" and "user list" 3 senarios
    connection = sqlite3.connect(db_url) #Connect to the db
    if connection.cursor().execute("SELECT count(*) FROM sqlite_master WHERE type='table';").fetchall()[0][0] < 1:
        cur = 0 #Check if the table already exists. If not, the index starts from 0
        connection.cursor().execute("CREATE TABLE IF NOT EXISTs History(HOSTNAMES TEXT, LAST_JOB TEXT, LAST_JOB_Account TEXT, LAST_JOB_JobId NUMBER,\
       LAST_JOB_UserId TEXT, LOAD NUMBER, OVERALL NUMBER, PING NUMBER, POWER NUMBER, REASON TEXT,\
       SCRATCH NUMBER, SLURMD_LOG TEXT, SOFTWARE NUMBER, SSH NUMBER, STATE TEXT, TIMESTAMP STRING, TMP NUMBER,\
       UPTIME NUMBER, USER TEXT, USER_BOOL NUMBER, Index_ID NUMBER, LogTime TIMESTAMP)")
        connection.cursor().execute("CREATE TABLE IF NOT EXISTs User(History_ID NUMBER, USER TEXT)")
        print ("yes")
    else:
        cur = connection.cursor().execute("SELECT COUNT(HOSTNAMES) FROM History").fetchall()[0][0] #If yes, start from the next index
    df["Index_ID"] = range(cur, cur + df.shape[0]) #Drop the column "SUGGESTION"
    df = df.reset_index(drop = True)
    df = df.drop(["SUGGESTION"], axis = 1)
    def user_table(df):
        user_df = pd.DataFrame()
        hist_l = []
        id_l = []
        for i in range(0,df.shape[0]):
            if df["USER_BOOL"][i] == "Yes":
                hist_l = hist_l + df["USER_PROCESSES"][i]
                id_l = id_l + [df["Index_ID"][i]] * len(df["USER_PROCESSES"][i])
        user_df["History_ID"] = id_l
        user_df["USER"] = hist_l
        return user_df   #Create a table that stores all of the users along with the id generated in History table
    user_df = user_table(df)
    df = df.drop(["USER_PROCESSES"], axis=1) #Drop "USER_PROCESS" for storage concerns
    connection = sqlite3.connect(db_url) #Connect to the db
    df["LogTime"] = [pd.Timestamp.now() for i in range(0,df.shape[0])]
    df.to_sql('History', con= connection,  if_exists = "append", index = False)
    user_df.to_sql("User", con= connection,  if_exists = "append", index = False) #Store the two tables
    print ("done")

def action(Hostname, Command, db_url):
    connection = sqlite3.connect(db_url)
    connection.cursor().execute("CREATE TABLE IF NOT EXISTs action(Hostname TEXT,Command TEXT, LogTime TIMESTAMP)")
    rows = (Hostname, Command, pd.datetime.now())
    connection.cursor().execute("INSERT INTO action values (?,?,?)", rows)
    connection.commit()
    print("done")

