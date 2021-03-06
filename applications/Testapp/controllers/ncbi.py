# -*- coding: utf-8 -*-

from Bio import Entrez, SeqIO, SeqFeature
from Bio.Seq import Seq
#from BioSQL import BioSeqDatabase
import glob
import os
import traceback
    

def email():
    # Request E-Mail for authenthication before proceding.
    print "email"
    email=FORM(INPUT(_name='email', requires=IS_NOT_EMPTY()), INPUT(_type='submit'))
    if email.process().accepted:
        session.email=email.vars.email
        session.flash="Email %s registered" %(session.email)
        redirect(URL('search'))
    return dict(term1="Email", term2=email)

def term():
    # Enter search term. Forward to 'search' --> choseDB. Come here from 'search'. 
    search=FORM(INPUT(_name='term', requires=IS_NOT_EMPTY()), INPUT(_type="submit"))
        
    if search.process().accepted:
        print "term ok"
        session.term=search.vars.term
        print session.term
        session.flash="Databases searched for %s" %(session.term)
        redirect(URL('search'))
    
    return dict(term1="Search Term", term2=search)

def choseDB():
    # Chose DB
    handle=Entrez.egquery(term=session.term)
    record=Entrez.read(handle)
    choice=[]
    for row in record["eGQueryResult"]:
        choice.append(row["MenuName"]+" = "+row["Count"]+" results")
    
    form=SQLFORM.factory(Field('Database', requires=IS_IN_SET(choice)))

    if form.process().accepted:
        dbsplit=form.vars.Database.split()
        
        for row in record["eGQueryResult"]:
            if row["MenuName"]==dbsplit[0]:
                session.db=row["DbName"]
                session.count=int(row["Count"])
                
        session.flash="Searching %s for %s" %(session.db, session.term)
        redirect(URL(search))
    
    return dict(term1="Chose which DB to search", term2=form)

def dlForm():
    # Ask wheter you want to download the files, if yes --> download!
    rbtnYesNo = FORM(TABLE(TR('Download the files?',SELECT(['Yes', 'No'], _name="download",requires=IS_IN_SET(['Yes', 'No'])))), TR("",INPUT(_type="submit",_value="Proceed")))

    if rbtnYesNo.process().accepted:
        print "Accepted"
        if rbtnYesNo.vars.download=='Yes':
            for dlId in recList:    
                print dlId
                ncbi_file = open("NCBI_Files/"+dlId+".xml", "w")
                response.flash="Downloading ID %s ..." %(dlId)
                fetch_handle = Entrez.efetch(session.db, retmode="xml", id=dlId)
                data = fetch_handle.read()
                ncbi_file.write(data)
                fetch_handle.close()
                ncbi_file.close()
                response.flash= "Going to download record %s" % (dlId)  
                db.ncbi.insert(IdList=dlId)      

    print db().select(db.ncbi.IdList)

    return dict(term0=db().select(db.ncbi.IdList), term1="Do you want to download the files?", term2=rbtnYesNo)    
    
def download():

    print "Preparing to downlod Files..."
    
    # Here we start with the 'true' searching. Now we have chosen a DB and a search term, and there we go.
    print "Searching for files..."
    handle=Entrez.esearch(session.db, session.term, retmax=session.count)
    record=Entrez.read(handle)
    handle.close()
    count=int(record["Count"])
    
    '''
    Create a List of entries found on entrez.
    Fill DB: Create a list of files on the system, compare it with IDs in the DB.
    Compare DB with Entrez records
    Download everything from Entrez not in the DB
    '''
    
    ### Create Lists...
    # ... of IDs found on entrez:
    recList=record['IdList']    
    session.recList=recList
    
    # ...of entries in DB
    dbIdList=[]
    for row in db(db.ncbi).select(db.ncbi.IdList):
        dbIdList.append(row.IdList)    

    # ...of Files in Folder: 
    dirList=os.listdir("NCBI_Files")
    fileIdList=[]
    for fname in dirList:
        splitted=fname.split('.')
        fileIdList.append(splitted[0])

    # Search if all Files are in DB (and if not then add them):
    print "Updating Database..."
    for elem in fileIdList:
        if elem not in dbIdList:
            db.ncbi.insert(IdList=elem)
            

    # Creating DB list again...
    dbIdList=[]
    for row in db(db.ncbi).select(db.ncbi.IdList):
        dbIdList.append(row.IdList)
    
    # ... and look which files to download
    print "Comparing files with DB..."
    recList=[dl for rec in recList if rec not in dbIdList]

    print "Following Files are going to be downloaded: "
    print recList
            
    # Download
    dload=raw_input("Do you want to download these files?")    
    
    if dload=='y':
        ending=".xml"
        for dlId in recList:    
            db.ncbi.insert(IdList=dlId)
            try:         
                ncbi_file = open("NCBI_Files/"+dlId+ending, "w")
            except:
                print "Fehler beim öffnen der angeforderten Datei %s" %(dlId)
            response.flash="Downloading ID %s ..." %(dlId)
            fetch_handle = Entrez.efetch(session.db, retmode="xml", id=dlId)
            data = fetch_handle.read()
            ncbi_file.write(data)
            fetch_handle.close()
            ncbi_file.close()
            response.flash= "Going to download record %s" % (dlId)  

def parse():
    
    '''
    Wichtige informationen, bzw. aufbau der struktur:
    Locus Tag: Entrezgene_gene --> Gene-ref --> Gene-ref_locus-tag --> HIV2gp6
    
    
    '''
    pars=raw_input("Do you want to parse the files?")
    if pars=='y':
        i=0
        print "Parsing files..."
        logfile=open("logfile.log", "a")
                
        for ID in session.recList:
            print ID
            logfile.write("Nächster Eintrag: \n\n\n\n\n\n\n")
            
            try:
                file=open("NCBI_Files/"+ID+".xml")
                rec=Entrez.read(file, "xml")
                for entry in rec:
                    logfile.writelines(str(entry)+'\n\n\n\n')
                    
                    print entry.keys()
                    
                    print "Länge: %s,\t Definition: %s" %(len(entry['GBSeq_sequence']), entry['GBSeq_definition'])
                    for elem in entry['GBSeq_feature-table']:
                        print "Feature types\n %s: %s" %(['GBFeature_quals']['GBQualifier']['GBQualifier_name'], entry['GBSeq_feature-table']['GBFeature_quals']['GBQualifier']['GBQualifier_value'])
                
                    
                    
                print "Nächster Eintrag: "
#                print rec
                i+=1
                if i==3:
                    break
                
            except IOError:
                print "One corrupt file, probably the .gitignore. " 
                        
        logfile.close
                
def testsession():
    
    db.ncbi.truncate()
    #~ 
    #~ db.ncbi.insert(IdList="Testeintrag")
#~ 
    #~ dbIdList=[]
    #~ for row in db(db.ncbi).select(db.ncbi.IdList):
        #~ dbIdList.append(row.IdList)
#~ 
    #~ print dbIdList
    redirect(URL('search'))

def search():  
    
    ts=""
    ts=raw_input("Run testsession?")
    if ts=='y':
        testsession()
      
    # Hauptroutine. Here we start and forward to every single step (email, db, term, download, parse...) and come back here again after it's done.
    if not session.email:
        redirect(URL('email'))
        
    Entrez.email=session.email

    if not session.term:
        redirect(URL('term'))

    if not session.db:
        redirect(URL('choseDB'))

    download()
               
    parse()
    
    
    print "Finished"
    print session.db, session.term
