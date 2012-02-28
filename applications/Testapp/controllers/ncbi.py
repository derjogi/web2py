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
    
    # get a list of file id's, compare them with db, if not in db then download (and write data and ID into DB... still to come).    
    print "Compare files with DB..."
    recList=record['IdList']
    print recList
    
    print "\n\n\nFiles in DB:"
    for row in db(db.ncbi).select(db.ncbi.IdList):
        print row

        if row.IdList in recList:
            recList.remove(row.IdList)

        
    # get dir "NCBI_Files/" and all Filenames
    # remove xml from filename
    # compare. if it's there: remove from reclist, if not, download! 
    
    dirList=os.listdir("NCBI_Files")
    i=0
    for fname in dirList:
        i+=1
        splitted=fname.split('.')
        if splitted[0] in recList:
            recList.remove(splitted[0])
        
        print fname
        
        file=open("NCBI_Files/"+fname)
        rec=Entrez.read(file)
        print "Nächster Eintrag: "
        print rec
        raw_input(file)
        file.close()
            
        if i==4:
            break
            
    print "Nach überprüfung: "
    print recList
    
    cont=raw_input("Continue?")
    if cont!="y":
        redirect(URL('search'))
        
    elif cont=="n":
        session.cont='no'
        
    # Download    
    for dlId in recList:    
        print dlId
        db.ncbi.insert(IdList=dlId)          
        ncbi_file = open("NCBI_Files/"+dlId+".xml", "w")
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
    
    
    for ID in db().select(db.ncbi.IdList):
        file="NCBI_Files/"+ID.IdList+".xml"
        
        rec=SeqIO.read(file, "xml")
        print "Nächster Eintrag: "
        print rec

def search():        
    # Hauptroutine. Here we start and forward to every single step (email, db, term, download, parse...) and come back here again after it's done.
    if not session.email:
        redirect(URL('email'))
        
    Entrez.email=session.email

    if not session.term:
        redirect(URL('term'))

    if not session.db:
        redirect(URL('choseDB'))
        
    cont=raw_input('Continue to create a list?  ')
    if cont == 'yes':
        download()
               
    parse()
    
    
    print "Finished"
    print session.db, session.term
