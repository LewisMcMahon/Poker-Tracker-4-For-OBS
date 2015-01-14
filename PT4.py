import psycopg2
import datetime
import os
import time
from decimal import Decimal
from pprint import pprint

username        = "HeDares"
currency        = "USD"
currencyConvert = False
countActive     = True
##use if you have sessons that go past midnight
timeOffset      =  0

secondsInDay    = 60*60*24
secondsInWeek   = secondsInDay*7
secondsInMonth  = secondsInDay*30
##remove this later
timeOffset = secondsInDay/2


def gettourneyData(username,currency):
    try:
        conn = psycopg2.connect("dbname='PT4 DB' user='postgres' host='localhost' password='postgres'")
    except:
        print "I am unable to connect to the database"
        
    cur = conn.cursor()
    
    cur.execute("""SELECT 
      player.player_name, 
      tourney_results.date_start, 
      tourney_results.date_end, 
      tourney_results.amt_won, 
      tourney_results.cnt_rebuy, 
      tourney_results.cnt_addon,
      tourney_results.cnt_bounty,
      tourney_summary.amt_buyin, 
      tourney_summary.amt_fee, 
      tourney_summary.amt_rebuy, 
      tourney_summary.amt_addon, 
      tourney_summary.amt_bounty, 
      tourney_summary.currency, 
      tourney_summary.val_curr_conv,
      tourney_results.val_finish,
      tourney_results.id_tourney
      
    FROM 
      public.tourney_summary, 
      public.player, 
      public.tourney_results
    WHERE 
      tourney_summary.id_tourney = tourney_results.id_tourney AND
      tourney_results.id_player = player.id_player AND
      player.player_name = '"""+str(username)+"""' AND 
      tourney_summary.currency = '"""+str(currency)+"""'
    ORDER BY
      tourney_results.date_start ASC;""")
    
    
    rows = cur.fetchall()
    
    tourneyData = []
    
    for row in rows:        
        tempDict = {"player_name"   : row[0],
                    "date_start"    : row[1],
                    "date_end"      : row[2],
                    "amt_won"       : row[3],
                    "cnt_rebuy"     : row[4],
                    "cnt_addon"     : row[5],
                    "cnt_bounty"    : row[6],
                    "amt_buyin"     : row[7],
                    "amt_fee"       : row[8],
                    "amt_rebuy"     : row[9],
                    "amt_addon"     : row[10],
                    "amt_bounty"    : row[11],
                    "currency"      : row[12],
                    "val_curr_conv" : row[13],
                    "val_finish"    : row[14],
                    "id_tourney"    : row[15]}
        tourneyData.append(tempDict)
        
    return tourneyData
   
def calcTournamentNetValue(tourneyRow):
    netWon = tourneyRow["amt_won"]
    netWon += (tourneyRow["amt_bounty"]*tourneyRow["cnt_bounty"])
    netWon -= (tourneyRow["amt_buyin"]+tourneyRow["amt_fee"]+(tourneyRow["amt_rebuy"]*tourneyRow["cnt_rebuy"])+(tourneyRow["amt_addon"]*tourneyRow["cnt_addon"]))
    #print str(netWon)+" "+str(tourneyRow["date_end"])
    
    
    ##convert to local curency in pt4 if set
    if currencyConvert == True:
        netWon = netWon*tourneyRow["val_curr_conv"]
            
    return netWon

def getEpoch(inputDateTime):
    return (inputDateTime-datetime.datetime(1970,1,1)).total_seconds()

def getStats(tourneyData):
    stats = {"Live" :           {"Net Won" : 0, "tournaments" : []}, 
            "Today" :           {"Net Won" : 0, "played" : 0, "hands" : 0}, 
            "Yesterday" :       {"Net Won" : 0, "played" : 0, "hands" : 0}, 
            "This Week" :       {"Net Won" : 0, "played" : 0, "hands" : 0}, 
            "This Month" :      {"Net Won" : 0, "played" : 0, "hands" : 0}, 
            "All Time":         {"Net Won" : 0, "played" : 0, "hands" : 0}
    }
    
    for tourney in tourneyData:
        tourneyNetWon = calcTournamentNetValue(tourney)
        
        tournamentStartDateADJ = datetime.datetime.fromtimestamp(getEpoch(tourney["date_end"])-timeOffset)
        
        #active
        if tourney["val_finish"] == "" and tournamentStartDateADJ.date() == datetime.datetime.now().date: 
            print "live"
                   
            if countActive == True and tourney["date_end"] == "":
                tourney["date_end"] = datetime.datetime.now()
            elif tourney["date_end"] == "":
                tourney["date_end"] = datetime.datetime.now()
                #tourneyNetWon = Decimal(0)
        
        #tooday
        if tournamentStartDateADJ.date() == datetime.datetime.now().date():
            stats["Today"]["Net Won"] = stats["Today"]["Net Won"]+tourneyNetWon
        
        #Yesterday    
        if tournamentStartDateADJ.date() == datetime.date.fromordinal(datetime.date.today().toordinal()-1):            
            stats["Yesterday"]["Net Won"] =  stats["Yesterday"]["Net Won"]+tourneyNetWon 
        
        #thisWeek
        weekStart = datetime.date.today() - datetime.timedelta(days = datetime.date.today().weekday())
        weekEnd = weekStart + datetime.timedelta(days = 6)
        
        if tournamentStartDateADJ.date() <= weekEnd and tournamentStartDateADJ.date() >= weekStart:
            stats["This Week"]["Net Won"] = stats["This Week"]["Net Won"]+tourneyNetWon
        
        #month
        if tournamentStartDateADJ.month == datetime.date.today().month:
            stats["This Month"]["Net Won"] = stats["This Month"]["Net Won"]+tourneyNetWon
                
        #all time
        stats["All Time"]["Net Won"] = stats["All Time"]["Net Won"]+tourneyNetWon
    return stats;

def writeFiles(stats):
    for timePoint in stats:
        if not os.path.exists(timePoint):
            os.makedirs(timePoint)
        if timePoint == "live":
            pass    
        else:
            for stat in stats[timePoint]:
                stats[timePoint][stat]
                statFile = open(timePoint+"/"+stat+".txt", "wb")
                statFile.write(timePoint+" "+stat+": $"+str(stats[timePoint][stat]))
                statFile.close()

while True == True:   
    writeFiles(getStats(gettourneyData(username,currency)))
    print "files Writen at "+str(datetime.datetime.time(datetime.datetime.now()))
    break
    time.sleep(30)























