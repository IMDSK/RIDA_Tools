"""
 Objective : This Script for Download Satellite data : Sentinel-2 from Copernicus Data Space Ecosystem
             referense https://dataspace.copernicus.eu/
             This Script is
               + Can be to autoamtic download by using Task scheduler on windows
               + will check with data to download already (not download)
               + will check on file to downlaod already but not compleate (failed file) and will redownload
               + can use many users and random user for protect limited from server service
               + can select image of Sentinel-2 by Tiles easy than by coordinate
Writer : Anusorn Rungsipanich : Gistda@2023, RESGAT@2023

log status
20231106 : Starting write script
20231113 : frist version 


"""
# import session
import datetime,os,subprocess,glob,csv,random,time
from datetime import timedelta
from datetime import date
import requests
import pandas as pd

#  Decare Session
# --- Decare log Floder ---
PathLog = 'satallite_image_acquire/log'  # Floder for keep log file


# --- Decare Option ---
DateOption = 1 # 1 = Number of from now, 2 = Start Day to End Day
NuDays = 5 # nuber of day from now with DateOption = 1
StartDay = '2022-11-06' # YYYYMMDD  Starting Date with DateOption = 2
EndDay = '2023-01-12' # YYYYMMDD Ending Date with DateOption = 2
SepDays = 10 # for separate day every SepDays No need to change 10 days is work

# --- Decare User Password ---

NuUser = 3 # Nuber os user
User01 = 'Desukaz.skrr@gmail.com' #user name 1
Pass01 = 'IMDSK7901Desuka!' #password user 1
User02 = 'Desukaz.skrr@gmail.com' #user name 2
Pass02 = 'IMDSK7901Desuka!'  #password user 2
User03 = 'Desukaz.skrr@gmail.com' #user name 3
Pass03 = 'IMDSK7901Desuka!'  #password user 3


MainSN = 'sentinel_image_aquire'  # Floder for keeping satellite data 

Sn2Levels = ['MSIL1C'] #['MSIL1C','MSIL2A'] option of level to download

aoi = "POLYGON((96.7 21.0,106.0 21.0,106.0 5.2,96.7 5.2,96.7 21.0))'" #Thailand rectangular boundary
data_collection = "SENTINEL-2" #SENTINEL-1,SENTINEL-2,SENTINEL-3,SENTINEL-5P

# Tiles = ['T47PRQ', 'T47PRR', 'T48PTA', 'T48PTV', 'T47PNQ', 'T47PNR', 'T47PNS', 'T47PPQ'] # Tile for download
Tiels = ['T47QNB']

#Perpare session
lstUser = []
lstPass = []
for u in range(NuUser):
    lstUser.append(globals()['User' +  str(u + 1).zfill(2)])
    lstPass.append(globals()['Pass' +  str(u + 1).zfill(2)])
                 

#Module session
def DateDolist():
    TDay = datetime.date.today()
    SYMD = TDay - timedelta(NuDays)
    EnD = TDay.strftime("%Y-%m-%d")
    StD = SYMD.strftime("%Y-%m-%d")
    return [StD,EnD]

def Sepby10day(lSE):
    lstSepSE = []
    for SE in lSE:
        FristStart = datetime.datetime.strptime(SE[0], '%Y-%m-%d')
        FristEnd = datetime.datetime.strptime(SE[1], '%Y-%m-%d') + datetime.timedelta(days = 1)
        #DeltaDay = FristEnd - FristStart
        #div = DeltaDay / datetime.timedelta(11)
        RunStartDay = FristStart
        while RunStartDay < FristEnd:
            RunEndDay = RunStartDay + datetime.timedelta(days = 10)
            if RunEndDay > FristEnd:
                RunEndDay = FristEnd
            lstSepSE.append([RunStartDay.strftime("%Y-%m-%d"),RunEndDay.strftime("%Y-%m-%d")])
            
            #print (RunStartDay,RunEndDay)
            RunStartDay = RunStartDay + datetime.timedelta(days = 10)
    return (lstSepSE)
        

def CalStrEnd():
    if DateOption == 1:
        DoDay = DateDolist()
        SDay = DoDay[0]
        EDay  = DoDay[1]
    elif DateOption == 2:
        SDay = StartDay # YYYY-MM-DD
        EDay = EndDay

    if SDay[:4] == EDay[:4]:
        listStrEnd = [[SDay,EDay]]
    else:
        listStrEnd = [[SDay,SDay[:5]+'12-31'],[EDay[:5]+'01-01',EDay]]
    lstSepStEn = Sepby10day(listStrEnd)
    return lstSepStEn

def get_keycloak(username: str, password: str) -> str:
    data = {"client_id": "cdse-public","username": username,"password": password,"grant_type": "password",}
    try:
        r = requests.post("https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",data=data,)
        r.raise_for_status()
    except Exception as e:
        raise Exception(f"Keycloak token creation failed. Reponse from the server was: {r.json()}")
    return r.json()["access_token"]
        


def SearchIdSN(SE,Tile):
    IdNameSen = []
    start_date = SE[0]
    end_date = SE[1]
    
    #json = requests.get(f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=Collection/Name eq '{data_collection}' and OData.CSC.Intersects(area=geography'SRID=4326;{aoi}) and ContentDate/Start gt {start_date}T00:00:00.000Z and ContentDate/Start lt {end_date}T00:00:00.000Z").json()
    #json = requests.get(f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=contains(Name,'T47PRS') and Collection/Name eq '{data_collection}' and OData.CSC.Intersects(area=geography'SRID=4326;{aoi}) and ContentDate/Start gt {start_date}T00:00:00.000Z and ContentDate/Start lt {end_date}T00:00:00.000Z").json()
    json = requests.get(f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=contains(Name,'{Tile}') and Collection/Name eq '{data_collection}' and OData.CSC.Intersects(area=geography'SRID=4326;{aoi}) and ContentDate/Start gt {start_date}T00:00:00.000Z and ContentDate/Start lt {end_date}T00:00:00.000Z").json()

    AllSn = pd.DataFrame.from_dict(json['value']).head(20)
    #my_list = list(AllSn)
    #print (my_list)
    
    IdNameSn = pd.DataFrame(AllSn, columns=['Id', 'Name','Checksum','ContentLength'])
    for index,row in IdNameSn.iterrows():
        IdNameSen.append ([row['Id'],row['Name'],row['Checksum'],row['ContentLength']])
    return IdNameSen


def CheckSenLevel(SEDay,Prod):
    PdFil = []
    if len(Prod):
        for PdT in Prod:
            NameProd = PdT[1][:-5] + '.zip'
            #print (NameProd)
            if (NameProd[4:10] in Sn2Levels):
                PdFil.append(PdT)
    return PdFil

def CheckSenArch(SEDay,Prod):
    PdFil = []
    YY = SEDay[0][:4]
    ActiveDir = MainSN + "/" + YY
    if not os.path.exists(ActiveDir):
        os.makedirs(ActiveDir)    
    os.chdir(ActiveDir)
    AcrNameList = glob.glob("*.zip")
    #print (AcrNameList)
    #AcrMainNameList = []
    if len(Prod):
        for PdT in Prod:
            NameProd = PdT[1][:-5] + '.zip'
            #print (NameProd,(NameProd in AcrNameList))
            if (NameProd in AcrNameList):
                sizefile = os.path.getsize(NameProd)
                #print (PdT[2][0]['Value'] , arhFile,os.path.getsize(NameProd),PdT[3])
                #if not (PdT[2][0]['Value'] == arhFile):
                if sizefile < PdT[3]:
                    os.remove(NameProd)
                    PdFil.append(PdT)
                    print("        * File size is smaller than original then Will Remove and reDownload : " + NameProd)
                    logFile.write("        * File size is smaller than original then Will Remove and reDownload : " + NameProd + "\n")
                    
            else:
                PdFil.append(PdT)
                print("        * Will Download : " + NameProd)
                logFile.write("        * Will Download : " + NameProd + "\n")
                
    return PdFil

def DownSen(SEDay,Prod):
    YY = SEDay[0][:4]
    ActiveDir = MainSN + "/" + YY
    os.chdir(ActiveDir)
    if len(Prod):
        for PdT in Prod:
            #for random change user
            randUser = random.randrange(NuUser)
            UserN = lstUser[randUser]
            PassW = lstPass[randUser]
            
            keycloak_token = get_keycloak(UserN, PassW)
            session = requests.Session()
            session.headers.update({'Authorization': f'Bearer {keycloak_token}'})
            print ("          + Using User : " + UserN + " to download.")
            logFile.write("          + Using User : " + UserN + " to download.\n")

            url = f'https://catalogue.dataspace.copernicus.eu/odata/v1/Products(' + PdT[0] + f')/$value'
            #print (url)
            NameProd = PdT[1][:-5] + '.zip'
            print ("          + Starting Download : " + str(datetime.datetime.now()) + " : " + NameProd)
            logFile.write("          + Starting Download : " + str(datetime.datetime.now()) + " : " + NameProd + "\n")
            response = session.get(url, allow_redirects=False)
            while response.status_code in (301, 302, 303, 307):
                url = response.headers['Location']
                response = session.get(url, allow_redirects=False)
            file = session.get(url, verify=False, allow_redirects=True)
            with open(NameProd, 'wb') as p:
                p.write(file.content)
            print ("          + Ending Download : " + str(datetime.datetime.now()) + " : " + NameProd)
            logFile.write("          + Ending Download : " + str(datetime.datetime.now()) + " : " + NameProd + "\n")


if __name__ == "__main__":
    logDate = datetime.datetime.now()
    logName = "DownSN_GISTDA_LOG_" + str(logDate.year) + str(logDate.month).zfill(2) + str(logDate.day).zfill(2) + str(logDate.hour).zfill(2) + str(logDate.minute).zfill(2) + ".txt"
    logFile = open(PathLog + "/" + logName, 'w')
    print ("  Download Sentinal-2 file")
    logFile.write('  Download Sentinal-2 file' + '\n')
    print ('  Script Download Sentinal-2 From Gistda/RESGAT Version 1.10')
    logFile.write('  Script Download Sentinal-2 From Gistda/RESGAT Version 1.10\n')
    #logFile.write("Process file since : ", date.today() - timedelta(NuDays) ," until ",date.today())
    print ("  Starting time is : " + str(datetime.datetime.now()))
    logFile.write("  Starting time is : " + str(datetime.datetime.now()) + "\n")

    StrEnd = CalStrEnd()
    #print (StrEnd[0][0])
    #for random change user
    randUser = random.randrange(NuUser)
    UserN = lstUser[randUser]
    PassW = lstPass[randUser]
    keycloak_token = get_keycloak(UserN, PassW)

    for SE in StrEnd:
        print ("      -   Search from " + SE[0] + " to " + SE[1])
        logFile.write("      -   Search from " + SE[0] + " to " + SE[1] + "\n")
        #Search file
        for Tile in Tiles:
            SN2Pd = SearchIdSN(SE,Tile)
            #Filter only level
            FilSN2Lev = CheckSenLevel(SE,SN2Pd)
            #print (FilSN2Lev)
            #filter if have in 
            FilSN2Pd = CheckSenArch(SE,FilSN2Lev)
            #print (FilSN2Pd)
            DownSen(SE,FilSN2Pd)

    #Round 2
    StrEnd = CalStrEnd()
    #print (StrEnd[0][0])
    #for random change user
    randUser = random.randrange(NuUser)
    UserN = lstUser[randUser]
    PassW = lstPass[randUser]
    keycloak_token = get_keycloak(UserN, PassW)

    for SE in StrEnd:
        print ("      -   Search from " + SE[0] + " to " + SE[1])
        logFile.write("      -   Search from " + SE[0] + " to " + SE[1] + "\n")
        #Search file
        for Tile in Tiles:
            SN2Pd = SearchIdSN(SE,Tile)
            #Filter only level
            FilSN2Lev = CheckSenLevel(SE,SN2Pd)
            #print (FilSN2Lev)
            #filter if have in 
            FilSN2Pd = CheckSenArch(SE,FilSN2Lev)
            #print (FilSN2Pd)
            DownSen(SE,FilSN2Pd)


    print ("  DONE Download Sentinal-2 !!!")
    logFile.write("  DONE Download Sentinal-2 !!!\n")
    print ("  Ending time is : " + str(datetime.datetime.now()))
    logFile.write("  Ending time is : " + str(datetime.datetime.now()) + "\n")

    logFile.close()        
    




