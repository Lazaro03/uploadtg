print('starting..')
from pyobigram.utils import sizeof_fmt,get_file_size,createID,nice_time
from pyobigram.client import ObigramClient,inlineQueryResultArticle
from MoodleClient import MoodleClient

from JDatabase import JsonDatabase
import zipfile
import os
import infos
import mediafire
import datetime
import time
import youtube
import NexCloudClient

from pydownloader.downloader import Downloader
from ProxyCloud import ProxyCloud
import ProxyCloud
import socket
import tlmedia
import S5Crypto


def downloadFile(downloader,filename,currentBits,totalBits,speed,time,args):
    try:
        bot = args[0]
        message = args[1]
        thread = args[2]
        if thread.getStore('stop'):
            downloader.stop()
        downloadingInfo = infos.createDownloading(filename,totalBits,currentBits,speed,time,tid=thread.id)
        bot.editMessageText(message,downloadingInfo)
    except Exception as ex: print(str(ex))
    pass

def uploadFile(filename,currentBits,totalBits,speed,time,args):
    try:
        bot = args[0]
        message = args[1]
        originalfile = args[2]
        thread = args[3]
        downloadingInfo = infos.createUploading(filename,totalBits,currentBits,speed,time,originalfile)
        bot.editMessageText(message,downloadingInfo)
    except Exception as ex: print(str(ex))
    pass

def processUploadFiles(filename,filesize,files,update,bot,message,thread=None,jdb=None):
    try:
        bot.editMessageText(message,'馃饾悘饾惈饾悶饾惄饾悮饾惈饾悮饾惂饾悵饾惃 饾惄饾悮饾惈饾悮 饾惉饾惍饾悰饾悽饾惈鈽�...')
        evidence = None
        fileid = None
        user_info = jdb.get_user(update.message.sender.username)
        cloudtype = user_info['cloudtype']
        proxy = ProxyCloud.parse(user_info['proxy'])
        if cloudtype == 'moodle':
            client = MoodleClient(user_info['moodle_user'],
                                  user_info['moodle_password'],
                                  user_info['moodle_host'],
                                  user_info['moodle_repo_id'],
                                  proxy=proxy)
            loged = client.login()
            itererr = 0
            if loged:
                if user_info['uploadtype'] == 'evidence':
                    evidences = client.getEvidences()
                    evidname = str(filename).split('.')[0]
                    for evid in evidences:
                        if evid['name'] == evidname:
                            evidence = evid
                            break
                    if evidence is None:
                        evidence = client.createEvidence(evidname)

                originalfile = ''
                if len(files)>1:
                    originalfile = filename
                draftlist = []
                for f in files:
                    f_size = get_file_size(f)
                    resp = None
                    iter = 0
                    token = False
                    if user_info['token']!=0:
                       token = True
                    xdlink = False
                    if user_info['xdmode']!=0:
                    	xdlink = True
                    while resp is None:
                          if user_info['uploadtype'] == 'evidence':
                             fileid,resp = client.upload_file(f,evidence,fileid,progressfunc=uploadFile,args=(bot,message,originalfile,thread),token=token,xdlink=xdlink)
                             draftlist.append(resp)
                          if user_info['uploadtype'] == 'draft':
                             fileid,resp = client.upload_file_draft(f,progressfunc=uploadFile,args=(bot,message,originalfile,thread),token=token,xdlink=xdlink)
                             draftlist.append(resp)
                          if user_info['uploadtype'] == 'perfil':
                             fileid,resp = client.upload_file_perfil(f,progressfunc=uploadFile,args=(bot,message,originalfile,thread),token=token,xdlink=xdlink)
                             draftlist.append(resp)
                          if user_info['uploadtype'] == 'blog':
                             fileid,resp = client.upload_file_blog(f,progressfunc=uploadFile,args=(bot,message,originalfile,thread),token=token,xdlink=xdlink)
                             draftlist.append(resp)
                          if user_info['uploadtype'] == 'calendar':
                             fileid,resp = client.upload_file_calendar(f,progressfunc=uploadFile,args=(bot,message,originalfile,thread),token=token,xdlink=xdlink)
                             draftlist.append(resp)
                          iter += 1
                          if iter>=10:
                              break
                    os.unlink(f)
                if user_info['uploadtype'] == 'evidence':
                    try:
                        client.saveEvidence(evidence)
                    except:pass
                return client
            else:
                bot.editMessageText(message,'鉂岎潗勷潗潗潗潗� 饾悶饾惂 饾惀饾悮 饾惄饾悮饾悹饾悽饾惂饾悮鉂�')
        elif cloudtype == 'cloud':
            tokenize = False
            if user_info['tokenize']!=0:
               tokenize = True
            bot.editMessageText(message,'馃饾悞饾惍饾悰饾悽饾悶饾惂饾悵饾惃 鈽� 饾悇饾惉饾惄饾悶饾惈饾悶 饾惁饾悽饾悶饾惂饾惌饾惈饾悮饾惉... 馃槃')
            host = user_info['moodle_host']
            user = user_info['moodle_user']
            passw = user_info['moodle_password']
            remotepath = user_info['dir']
            client = NexCloudClient.NexCloudClient(user,passw,host,proxy=proxy)
            loged = client.login()
            if loged:
               originalfile = ''
               if len(files)>1:
                    originalfile = filename
               filesdata = []
               for f in files:
                   data = client.upload_file(f,path=remotepath,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                   filesdata.append(data)
                   os.unlink(f)
               return filesdata
        return None
    except Exception as ex:
        bot.editMessageText(message,f'鉂岎潗勷潗潗潗潗� {str(ex)}鉂�')


def processFile(update,bot,message,file,thread=None,jdb=None):
    file_size = get_file_size(file)
    getUser = jdb.get_user(update.message.sender.username)
    max_file_size = 1024 * 1024 * getUser['zips']
    file_upload_count = 0
    client = None
    findex = 0
    if file_size > max_file_size:
        compresingInfo = infos.createCompresing(file,file_size,max_file_size)
        bot.editMessageText(message,compresingInfo)
        zipname = str(file).split('.')[0] + createID()
        mult_file = zipfile.MultiFile(zipname,max_file_size)
        zip = zipfile.ZipFile(mult_file,  mode='w', compression=zipfile.ZIP_DEFLATED)
        zip.write(file)
        zip.close()
        mult_file.close()
        client = processUploadFiles(file,file_size,mult_file.files,update,bot,message,jdb=jdb)
        try:
            os.unlink(file)
        except:pass
        file_upload_count = len(zipfile.files)
    else:
        client = processUploadFiles(file,file_size,[file],update,bot,message,jdb=jdb)
        file_upload_count = 1
    bot.editMessageText(message,'馃槍饾悘饾惈饾悶饾惄饾悮饾惈饾悮饾惂饾悵饾惃 饾悮饾惈饾悳饾悺饾悽饾惎饾惃馃搫...')
    evidname = ''
    files = []
    if client:
        if getUser['cloudtype'] == 'moodle':
            if getUser['uploadtype'] == 'evidence':
                try:
                    evidname = str(file).split('.')[0]
                    txtname = evidname + '.txt'
                    evidences = client.getEvidences()
                    for ev in evidences:
                        if ev['name'] == evidname:
                           files = ev['files']
                           break
                        if len(ev['files'])>0:
                           findex+=1
                    client.logout()
                except:pass
            if getUser['uploadtype'] == 'draft' or getUser['uploadtype'] == 'blog' or getUser['uploadtype'] == 'calendar':
               for draft in client:
                   files.append({'name':draft['file'],'directurl':draft['url']})
        else:
            for data in client:
                files.append({'name':data['name'],'directurl':data['url']})
        bot.deleteMessage(message.chat.id,message.message_id)
        finishInfo = infos.createFinishUploading(file,file_size,max_file_size,file_upload_count,file_upload_count,findex)
        filesInfo = infos.createFileMsg(file,files)
        bot.sendMessage(message.chat.id,finishInfo+'\n'+filesInfo,parse_mode='html')
        if len(files)>0:
            txtname = str(file).split('/')[-1].split('.')[0] + '.txt'
            sendTxt(txtname,files,update,bot)
    else:
        bot.editMessageText(message,'鉂岎潗勷潗潗潗潗� 饾悶饾惂 饾惀饾悮 饾惄饾悮饾悹饾悽饾惂饾悮鉂�')

def ddl(update,bot,message,url,file_name='',thread=None,jdb=None):
    downloader = Downloader()
    file = downloader.download_url(url,progressfunc=downloadFile,args=(bot,message,thread))
    if not downloader.stoping:
        if file:
            processFile(update,bot,message,file,jdb=jdb)
        else:
            bot.editMessageText(message,'鉂岎潗勷潗ю潗ヰ潗氿潗滒潗� 饾惂饾惃 饾惄饾惈饾惃饾悳饾悶饾惉饾悮饾悵饾惃鉂�')

# def megadl(update,bot,message,megaurl,file_name='',thread=None,jdb=None):
#     megadl = megacli.mega.Mega({'verbose': True})
#     megadl.login()
#     try:
#         info = megadl.get_public_url_info(megaurl)
#         file_name = info['name']
#         megadl.download_url(megaurl,dest_path=None,dest_filename=file_name,progressfunc=downloadFile,args=(bot,message,thread))
#         if not megadl.stoping:
#             processFile(update,bot,message,file_name,thread=thread)
#     except:
#         files = megaf.get_files_from_folder(megaurl)
#         for f in files:
#             file_name = f['name']
#             megadl._download_file(f['handle'],f['key'],dest_path=None,dest_filename=file_name,is_public=False,progressfunc=downloadFile,args=(bot,message,thread),f_data=f['data'])
#             if not megadl.stoping:
#                 processFile(update,bot,message,file_name,thread=thread)
#         pass
#     pass

def sendTxt(name,files,update,bot):
                txt = open(name,'w')
                fi = 0
                for f in files:
                    separator = ''
                    if fi < len(files)-1:
                        separator += '\n'
                    txt.write(f['directurl']+separator)
                    fi += 1
                txt.close()
                bot.sendFile(update.message.chat.id,name)
                os.unlink(name)

def onmessage(update,bot:ObigramClient):
    try:
        thread = bot.this_thread
        username = update.message.sender.username
        tl_admin_user = os.environ.get('administrador')
        
        #set
        tl_admin_user = 'socram_Agm'

        jdb = JsonDatabase('database')
        jdb.check_create()
        jdb.load()

        user_info = jdb.get_user(username)

        if username == tl_admin_user or user_info :  # validate user
            if user_info is None:
                if username == tl_admin_user:
                    jdb.create_admin(username)
                else:
                    jdb.create_user(username)
                user_info = jdb.get_user(username)
                jdb.save()
        else:return


        msgText = ''
        try: msgText = update.message.text
        except:pass

        # comandos de admin
        if '/add' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                try:
                    user = str(msgText).split(' ')[1]
                    jdb.create_user(user)
                    jdb.save()
                    msg = '馃槈饾悥饾惃饾惃饾惃饾惏 @'+user+' 饾悮饾悺饾惃饾惈饾悮 饾惌饾悽饾悶饾惂饾悶饾惉 饾悮饾悳饾悳饾悶饾惉饾惃 饾悮饾惀 饾悰饾惃饾惌 饾悞饾惄饾悶饾悶饾悵饾悢饾惄饾惀饾惃饾悮饾悵饾悶饾惈 饾悞饾悶饾惈饾惎饾悽饾悳饾悶 饾惎7.3'
                    bot.sendMessage(update.message.chat.id,msg)
                except:
                    bot.sendMessage(update.message.chat.id,'鉂岎潗勷潗潗潗潗� 饾悶饾惂 饾悶饾惀 饾悳饾惃饾惁饾悮饾惂饾悵饾惃鉂�')
            else:
                bot.sendMessage(update.message.chat.id,'鉂岎潗嶐潗� 饾惌饾悽饾悶饾惂饾悶饾惉 饾惄饾悶饾惈饾惁饾悽饾惉饾惃 饾惄饾悮饾惈饾悮 饾悶饾惉饾惌饾惃鉂�')
            return
        if '/ban' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                try:
                    user = str(msgText).split(' ')[1]
                    if user == username:
                        bot.sendMessage(update.message.chat.id,'鉂岎潗嶐潗� 饾惉饾悶 饾惄饾惍饾悶饾悵饾悶 饾悰饾悮饾惂饾悶饾悮饾惈 饾悮 饾惍饾惉饾惌饾悶饾悵 饾惁饾悽饾惉饾惁饾惃鉂�')
                        return
                    jdb.remove(user)
                    jdb.save()
                    msg = '馃が饾悇饾惀 饾惍饾惉饾惍饾悮饾惈饾悽饾惃 @'+user+' 饾悮 饾惉饾悽饾悵饾惃 饾悰饾悮饾惂饾悶饾悮饾悵饾惃鉂�'
                    bot.sendMessage(update.message.chat.id,msg)
                except:
                    bot.sendMessage(update.message.chat.id,'鉂岎潗勷潗潗潗潗� 饾悶饾惂 饾悶饾惀 饾悳饾惃饾惁饾悮饾惂饾悵饾惃鉂�')
            else:
                bot.sendMessage(update.message.chat.id,'鉂岎潗嶐潗� 饾惌饾悽饾悶饾惂饾悶饾惉 饾惄饾悶饾惈饾惁饾悽饾惉饾惃 饾惄饾悮饾惈饾悮 饾悶饾惉饾惌饾惃鉂�')
            return
        if '/db' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                bot.sendMessage(update.message.chat.id,'馃梻锔忦潗侌潗氿潗潗� 饾悵饾悶 饾悵饾悮饾惌饾惃饾惉馃憞')
                bot.sendFile(update.message.chat.id,'database.jdb')
            else:
                bot.sendMessage(update.message.chat.id,'鉂岎潗嶐潗� 饾惌饾悽饾悶饾惂饾悶饾惉 饾惄饾悶饾惈饾惁饾悽饾惉饾惃 饾惄饾悮饾惈饾悮 饾悶饾惉饾惌饾惃鉂�')
            return

        if '/tuto' in msgText:
            tuto = open('tuto.txt','r')
            bot.sendMessage(update.message.chat.id,tuto.read())
            tuto.close()
            return

        if '/crypt' in msgText:
            proxy_sms = str(msgText).split(' ')[1]
            proxy = S5Crypto.encrypt(f'{proxy_sms}')
            bot.sendMessage(update.message.chat.id, f'馃懁饾悇饾惂饾悳饾惈饾惒饾惄饾惌饾悮饾悵饾惃:\n{proxy}')
            return

        if '/decrypt' in msgText:
            proxy_sms = str(msgText).split(' ')[1]
            proxy_de = S5Crypto.decrypt(f'{proxy_sms}')
            bot.sendMessage(update.message.chat.id, f'馃鈥嶐煉拣潗凁潗烉潗潗烉潗ю潗滒潗潗拆潗潗潗氿潗濔潗�:\n{proxy_de}')
            return
        if '/off_proxy' in msgText:
            try:
                getUser = user_info
                if getUser:
                    getUser['proxy'] = ''
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,'馃挃饾悘饾惈饾惃饾惐饾惒 饾悵饾悶饾惉饾悮饾悳饾惌饾悽饾惎饾悮饾悵饾惃 饾悳饾惃饾惂 饾悶饾惐饾悽饾惌饾惃')
            except:
                if user_info:
                    user_info['proxy'] = ''
                    statInfo = infos.createStat(username,user_info,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,'馃挃饾悘饾惈饾惃饾惐饾惒 饾悵饾悶饾惉饾悮饾悳饾惌饾悽饾惎饾悮饾悵饾惃 饾悳饾惃饾惂 饾悶饾惐饾悽饾惌饾惃')
            return
        if '/view_proxy' in msgText:
            try:


                getUser = user_info

                if getUser:
                    proxy = getUser['proxy']
                    bot.sendMessage(update.message.chat.id,proxy)
            except:
                if user_info:
                    proxy = user_info['proxy']
                    bot.sendMessage(update.message.chat.id,proxy)
            return
        if '/my' in msgText:
            getUser = user_info
            if getUser:
                statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                bot.sendMessage(update.message.chat.id,statInfo)
                return
        if '/zips' in msgText:
            getUser = user_info
            if getUser:
                try:
                   size = int(str(msgText).split(' ')[1])
                   getUser['zips'] = size
                   jdb.save_data_user(username,getUser)
                   jdb.save()
                   msg = '馃摎饾悑饾惃饾惉 饾惓饾悽饾惄饾惉 饾惉饾悶饾惈饾悮饾惂 饾悵饾悶 '+ sizeof_fmt(size*1024*1024)+' 饾惀饾悮饾惉 饾惄饾悮饾惈饾惌饾悶饾惉'
                   bot.sendMessage(update.message.chat.id,msg)
                except:
                   bot.sendMessage(update.message.chat.id,'鉂岎潗勷潗潗潗潗� 饾悶饾惂 饾悶饾惀 饾悳饾惃饾惁饾悮饾惂饾悵饾惃鉂�')    
                return
        if '/acc' in msgText:
            try:
                account = str(msgText).split(' ',2)[1].split(',')
                user = account[0]
                passw = account[1]
                getUser = user_info
                if getUser:
                    getUser['moodle_user'] = user
                    getUser['moodle_password'] = passw
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                bot.sendMessage(update.message.chat.id,'鉂岎潗勷潗潗潗潗� 饾悶饾惂 饾悶饾惀 饾悳饾惃饾惁饾悮饾惂饾悵饾惃鉂�')
            return
        if '/host' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                host = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['moodle_host'] = host
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                bot.sendMessage(update.message.chat.id,'鉂岎潗勷潗潗潗潗� 饾悶饾惂 饾悶饾惀 饾悳饾惃饾惁饾悮饾惂饾悵饾惃鉂�')
            return
        if '/repo' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                repoid = int(cmd[1])
                getUser = user_info
                if getUser:
                    getUser['moodle_repo_id'] = repoid
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                bot.sendMessage(update.message.chat.id,'鉂岎潗勷潗潗潗潗� 饾悶饾惂 饾悶饾惀 饾悳饾惃饾惁饾悮饾惂饾悵饾惃鉂�')
            return
        if '/xdlink_on' in msgText:
            try:
                getUser = user_info
                if getUser:
                    getUser['xdmode'] = 1
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                bot.sendMessage(update.message.chat.id,'鉂岎潗勷潗潗潗潗� 饾悶饾惂 饾悶饾惀 饾悳饾惃饾惁饾悮饾惂饾悵饾惃鉂�')
            return
        if '/xdlink_off' in msgText:
            try:
                getUser = user_info
                if getUser:
                    getUser['xdmode'] = 0
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                bot.sendMessage(update.message.chat.id,'鉂岎潗勷潗潗潗潗� 饾悶饾惂 饾悶饾惀 饾悳饾惃饾惁饾悮饾惂饾悵饾惃鉂�')
            return
        if '/token_on' in msgText:
            try:
                getUser = user_info
                if getUser:
                    getUser['token'] = 1
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                bot.sendMessage(update.message.chat.id,'鉂岎潗勷潗潗潗潗� 饾悶饾惂 饾悶饾惀 饾悳饾惃饾惁饾悮饾惂饾悵饾惃鉂�')
            return
        if '/token_off' in msgText:
            try:
                getUser = user_info
                if getUser:
                    getUser['token'] = 0
                    jdb.save_data_user(username,getUser)
             statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                bot.sendMessage(update.message.chat.id,'鉂岎潗勷潗潗潗潗� 饾悶饾惂 饾悶饾惀 饾悳饾惃饾惁饾悮饾惂饾悵饾惃鉂�')
            return
        if '/cloud' in msgText:
            try:
                cmd = str(msgText).split(' ')[0]
                getUser = user_info
                if getUser:
                    getUser['cloudtype'] = cmd
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                bot.sendMessage(update.message.chat.id,'鉂岎潗勷潗潗潗潗� 饾悶饾惂 饾悶饾惀 饾悳饾惃饾惁饾悮饾惂饾悵饾惃鉂�')
            return
        if '/up' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                type = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['uploadtype'] = type
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                bot.sendMessage(update.message.chat.id,'鉂岎潗勷潗潗潗潗� 饾悶饾惂 饾悶饾惀 饾悳饾惃饾惁饾悮饾惂饾悵饾惃鉂�')
            return
        if '/proxy' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                proxy = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['proxy'] = proxy
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                if user_info:
                    user_info['proxy'] = ''
                    statInfo = infos.createStat(username,user_info,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            return
        if '/off_proxy' in msgText:
            try:
                getUser = user_info
                if getUser:
                    getUser['proxy'] = ''
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                if user_info:
                    user_info['proxy'] = ''
                    statInfo = infos.createStat(username,user_info,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            return
            
        if '/cancel_' in msgText:
            try:
                cmd = str(msgText).split('_',2)
                tid = cmd[1]
                tcancel = bot.threads[tid]
                msg = tcancel.getStore('msg')
                tcancel.store('stop',True)
                time.sleep(3)
                bot.editMessageText(msg,'鉂岎潗凁潗烉潗潗滒潗氿潗潗狆潗� 饾悳饾悮饾惂饾惉饾悶饾惀饾悮饾悵饾悮鉂�')
            except Exception as ex:
                print(str(ex))
            return
 
        message = bot.sendMessage(update.message.chat.id,'鉁岎煒滒潗�饾惂饾悮饾惀饾悽饾惓饾悮饾惂饾悵饾惃...')

        thread.store('msg',message)
        if '/start' in msgText:
            start_msg= '馃饾悂饾惃饾惌: 饾悞饾惄饾悶饾悶饾悵饾悢饾惄饾惀饾惃饾悮饾悵饾悶饾惈 饾悞饾悶饾惈饾惎饾悽饾悳饾悶 饾惎7.3\n馃帺饾悆饾悶饾惉饾悮饾惈饾惈饾惃饾惀饾惀饾悮饾悵饾惃饾惈: @xXxWTF_Dev\n馃枊饾悆饾悽饾惉饾悶饾惂虄饾悮饾悵饾惃饾惈: @Jose_752\n馃敟饾悡饾惃饾悵饾惃饾惉 饾惀饾惃饾惉 饾悳饾惃饾惁饾悮饾惂饾悵饾惃饾惉 饾悵饾悶饾惀 饾悰饾惃饾惌 饾惉饾惃饾惂 饾悳饾惃饾惁饾惄饾惀饾悶饾惌饾悮饾惁饾悶饾惂饾惌饾悶 饾悷饾惍饾惂饾悳饾悽饾惃饾惂饾悮饾惀饾悶饾惉 饾悮饾惉饾悽 饾惇饾惍饾悶 饾惌饾悶 饾惈饾悶饾悳饾惃饾惁饾悶饾惂饾悵饾悮饾惁饾惃饾惉 饾惇饾惍饾悶 饾惍饾惉饾悶饾惉 饾悶饾惀 /tuto'
            bot.editMessageText(message,start_msg)
        elif '/files' == msgText and user_info['cloudtype']=='moodle':
             proxy = ProxyCloud.parse(user_info['proxy'])
             client = MoodleClient(user_info['moodle_user'],
                                   user_info['moodle_password'],
                                   user_info['moodle_host'],
                                   user_info['moodle_repo_id'],proxy=proxy)
             loged = client.login()
             if loged:
                 files = client.getEvidences()
                 filesInfo = infos.createFilesMsg(files)
                 bot.editMessageText(message,filesInfo)
                 client.logout()
             else:
                bot.editMessageText(message,'鉂岎潗勷潗潗潗潗� 饾惒 饾悅饾悮饾惍饾惉饾悮饾惉馃槫\n1-饾悜饾悶饾惎饾悽饾惉饾悶 饾惉饾惍 饾悅饾惍饾悶饾惂饾惌饾悮\n2-饾悞饾悶饾惈饾惎饾悽饾悵饾惃饾惈 饾悆饾悶饾惉饾悮饾悰饾悽饾惀饾悽饾惌饾悮饾悵饾惃: '+client.path)
        elif '/txt_' in msgText and user_info['cloudtype']=='moodle':
             findex = str(msgText).split('_')[1]
             findex = int(findex)
             proxy = ProxyCloud.parse(user_info['proxy'])
             client = MoodleClient(user_info['moodle_user'],
                                   user_info['moodle_password'],
                                   user_info['moodle_host'],
                                   user_info['moodle_repo_id'],proxy=proxy)
             loged = client.login()
             if loged:
                 evidences = client.getEvidences()
                 evindex = evidences[findex]
                 txtname = evindex['name']+'.txt'
                 sendTxt(txtname,evindex['files'],update,bot)
                 client.logout()
                 bot.editMessageText(message,'馃搫饾悡饾惐饾悡 饾悁饾惇饾惍饾悽馃憞')
             else:
                bot.editMessageText(message,'鉂岎潗勷潗潗潗潗� 饾惒 饾悅饾悮饾惍饾惉饾悮饾惉馃槫\n1-饾悜饾悶饾惎饾悽饾惉饾悶 饾惉饾惍 饾悅饾惍饾悶饾惂饾惌饾悮\n2-饾悞饾悶饾惈饾惎饾悽饾悵饾惃饾惈 饾悆饾悶饾惉饾悮饾悰饾悽饾惀饾悽饾惌饾悮饾悵饾惃: '+client.path)
             pass
        elif '/del_' in msgText and user_info['cloudtype']=='moodle':
            findex = int(str(msgText).split('_')[1])
            proxy = ProxyCloud.parse(user_info['proxy'])
            client = MoodleClient(user_info['moodle_user'],
                                   user_info['moodle_password'],
                                   user_info['moodle_host'],
                                   user_info['moodle_repo_id'],
                                   proxy=proxy)
            loged = client.login()
            if loged:
                evfile = client.getEvidences()[findex]
                client.deleteEvidence(evfile)
                client.logout()
                bot.editMessageText(message,'馃棏饾悁饾惈饾悳饾悺饾悽饾惎饾惃 饾悰饾惃饾惈饾惈饾悮饾悵饾惃馃棏')
            else:
                bot.editMessageText(message,'鉂岎潗勷潗潗潗潗� 饾惒 饾悅饾悮饾惍饾惉饾悮饾惉馃槫\n1-饾悜饾悶饾惎饾悽饾惉饾悶 饾惉饾惍 饾悅饾惍饾悶饾惂饾惌饾悮\n2-饾悞饾悶饾惈饾惎饾悽饾悵饾惃饾惈 饾悆饾悶饾惉饾悮饾悰饾悽饾惀饾悽饾惌饾悮饾悵饾惃: '+client.path)
        elif '/delall' in msgText and user_info['cloudtype']=='moodle':
            proxy = ProxyCloud.parse(user_info['proxy'])
            client = MoodleClient(user_info['moodle_user'],
                                   user_info['moodle_password'],
                                   user_info['moodle_host'],
                                   user_info['moodle_repo_id'],
                                   proxy=proxy)
            loged = client.login()
            if loged:
                evfiles = client.getEvidences()
                for item in evfiles:
                	client.deleteEvidence(item)
                client.logout()
                bot.editMessageText(message,'馃棏饾悁饾惈饾悳饾悺饾悽饾惎饾惃饾惉 饾悵饾悶 饾惀饾悮 饾惂饾惍饾悰饾悶 饾悰饾惃饾惈饾惈饾悮饾悵饾惃饾惉馃棏')
            else:
                bot.editMessageText(message,'鉂岎潗勷潗潗潗潗� 饾惒 饾悅饾悮饾惍饾惉饾悮饾惉馃槫\n1-饾悜饾悶饾惎饾悽饾惉饾悶 饾惉饾惍 饾悅饾惍饾悶饾惂饾惌饾悮\n2-饾悞饾悶饾惈饾惎饾悽饾悵饾惃饾惈 饾悆饾悶饾惉饾悮饾悰饾悽饾惀饾悽饾惌饾悮饾悵饾惃: '+client.path)       
        elif 'http' in msgText:
            url = msgText
            ddl(update,bot,message,url,file_name='',thread=thread,jdb=jdb)
        else:
            #if update:
            #    api_id = os.environ.get('api_id')
            #    api_hash = os.environ.get('api_hash')
            #    bot_token = os.environ.get('bot_token')
            #    
                # set in debug
            #    api_id = 21886311
            #    api_hash = '7a9525470d5740e16fbfedfe2960c49a'
            #    bot_token = '5918605660:AAGYOfuqTEiclMHc6gLfBHu_Bda6531phjQ'

            #    chat_id = int(update.message.chat.id)
            #    message_id = int(update.message.message_id)
            #    import asyncio
            #    asyncio.run(tlmedia.download_media(api_id,api_hash,bot_token,chat_id,message_id))
            #    return
            bot.editMessageText(message,'馃槫饾悕饾惃 饾惉饾悶 饾惄饾惍饾悵饾惃 饾惄饾惈饾惃饾悳饾悶饾惉饾悮饾惈馃槫')
    except Exception as ex:
           print(str(ex))
print('Ready')
def main():
    bot_token = os.environ.get('bot_token')
    
    #set
    bot_token = '5918605660:AAGYOfuqTEiclMHc6gLfBHu_Bda6531phjQ'

    bot = ObigramClient(bot_token)
    bot.onMessage(onmessage)
    bot.run()

if __name__ == '__main__':
    try:
        main()
    except:
        main()

