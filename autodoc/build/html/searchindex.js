Search.setIndex({docnames:["hypernode","index","modules"],envversion:53,filenames:["hypernode.rst","index.rst","modules.rst"],objects:{"":{base58:[2,0,0,"-"],com_helpers:[2,0,0,"-"],config:[2,0,0,"-"],determine:[2,0,0,"-"],hn_client:[0,0,0,"-"],hn_instance:[0,0,0,"-"],posblock:[2,0,0,"-"],poschain:[2,0,0,"-"],posclient:[2,0,0,"-"],poscrypto:[2,0,0,"-"],poshelpers:[2,0,0,"-"],poshn:[2,0,0,"-"],posmempool:[2,0,0,"-"],sqlitebase:[2,0,0,"-"]},"posblock.PosBlock":{add_to_proto:[2,4,1,""],from_dict:[2,4,1,""],from_proto:[2,4,1,""],hex_encodable:[2,5,1,""],old_digest_block:[2,4,1,""],props:[2,5,1,""],sign:[2,4,1,""],status:[2,4,1,""],to_db:[2,4,1,""],to_dict:[2,4,1,""],to_json:[2,4,1,""],to_proto:[2,4,1,""],to_raw:[2,4,1,""]},"posblock.PosHeight":{from_dict:[2,4,1,""],from_proto:[2,4,1,""],hex_encodable:[2,5,1,""],props:[2,5,1,""],to_dict:[2,4,1,""],to_proto:[2,4,1,""]},"posblock.PosMessage":{add_to_proto:[2,4,1,""],add_to_proto_block:[2,4,1,""],check:[2,4,1,""],from_dict:[2,4,1,""],from_list:[2,4,1,""],from_proto:[2,4,1,""],from_values:[2,4,1,""],hex_encodable:[2,5,1,""],props:[2,5,1,""],sign:[2,4,1,""],to_db:[2,4,1,""],to_json:[2,4,1,""],to_list:[2,4,1,""],to_raw:[2,4,1,""]},"poschain.MemoryPosChain":{status:[2,4,1,""]},"poschain.PosChain":{_height_status:[2,4,1,""],_insert_block:[2,4,1,""],_invalidate:[2,4,1,""],_last_block:[2,4,1,""],async_blockinfo:[2,4,1,""],async_height:[2,4,1,""],check_round:[2,4,1,""],digest_block:[2,4,1,""],genesis_block:[2,4,1,""],last_block:[2,4,1,""],rollback:[2,4,1,""],status:[2,4,1,""],tx_exists:[2,4,1,""]},"poschain.SqlitePosChain":{_height_status:[2,4,1,""],_insert_block:[2,4,1,""],_last_block:[2,4,1,""],async_active_hns:[2,4,1,""],async_blockinfo:[2,4,1,""],async_blocksync:[2,4,1,""],async_getaddtxs:[2,4,1,""],async_getblock:[2,4,1,""],async_getheaders:[2,4,1,""],async_gettx:[2,4,1,""],async_roundblocks:[2,4,1,""],check:[2,4,1,""],delete_round:[2,4,1,""],rollback:[2,4,1,""],status:[2,4,1,""],tx_exists:[2,4,1,""]},"posclient.Posclient":{action:[2,4,1,""]},"poshn.HNState":{CATCHING_UP_CONNECT1:[2,5,1,""],CATCHING_UP_CONNECT2:[2,5,1,""],CATCHING_UP_ELECT:[2,5,1,""],CATCHING_UP_PRESYNC:[2,5,1,""],CATCHING_UP_SYNC:[2,5,1,""],FORGING:[2,5,1,""],MINIMAL_CONSENSUS:[2,5,1,""],ROUND_SYNC:[2,5,1,""],SENDING:[2,5,1,""],START:[2,5,1,""],STRONG_CONSENSUS:[2,5,1,""],SYNCING:[2,5,1,""],TESTING:[2,5,1,""]},"poshn.HnServer":{_handle_msg:[2,4,1,""],handle_stream:[2,4,1,""],update:[2,4,1,""]},"poshn.Poshn":{_consensus:[2,4,1,""],_exchange_height:[2,4,1,""],_exchange_mempool:[2,4,1,""],_get_peer_stream:[2,4,1,""],_get_round_blocks:[2,4,1,""],_new_tx:[2,4,1,""],_round_sync:[2,4,1,""],_update_network:[2,4,1,""],add_inbound:[2,4,1,""],change_state_to:[2,4,1,""],check_os:[2,4,1,""],check_round:[2,4,1,""],client_worker:[2,4,1,""],clients:[2,5,1,""],connect:[2,4,1,""],digest_height:[2,4,1,""],digest_txs:[2,4,1,""],forge:[2,4,1,""],get_hypernodes:[2,4,1,""],hello_string:[2,4,1,""],inbound:[2,5,1,""],init_check:[2,4,1,""],init_log:[2,4,1,""],manager:[2,4,1,""],post_block:[2,4,1,""],refresh_last_block:[2,4,1,""],remove_inbound:[2,4,1,""],round_status:[2,4,1,""],serve:[2,4,1,""],status:[2,4,1,""],stop:[2,4,1,""],stop_event:[2,5,1,""],update_inbound:[2,4,1,""]},"posmempool.MemoryMempool":{_delete_tx:[2,4,1,""],_insert_tx:[2,4,1,""],status:[2,4,1,""]},"posmempool.Mempool":{_delete_tx:[2,4,1,""],_insert_tx:[2,4,1,""],async_all:[2,4,1,""],digest_tx:[2,4,1,""],status:[2,4,1,""],tx_count:[2,4,1,""],tx_exists:[2,4,1,""]},"posmempool.SqliteMempool":{_insert_tx:[2,4,1,""],async_all:[2,4,1,""],async_alltxids:[2,4,1,""],async_del_txids:[2,4,1,""],async_purge:[2,4,1,""],async_purge_start:[2,4,1,""],async_since:[2,4,1,""],check:[2,4,1,""],clear:[2,4,1,""],status:[2,4,1,""],tx_count:[2,4,1,""],tx_exists:[2,4,1,""]},"sqlitebase.SqliteBase":{async_close:[2,4,1,""],async_commit:[2,4,1,""],async_execute:[2,4,1,""],async_fetchall:[2,4,1,""],async_fetchone:[2,4,1,""],async_vacuum:[2,4,1,""],check:[2,4,1,""],close:[2,4,1,""],commit:[2,4,1,""],execute:[2,4,1,""],fetch_one:[2,4,1,""]},base58:{b58decode:[2,1,1,""],b58decode_int:[2,1,1,""],b58encode:[2,1,1,""],b58encode_int:[2,1,1,""],buffer:[2,1,1,""],iseq:[2,1,1,""],scrub_input:[2,1,1,""]},com_helpers:{async_receive:[2,1,1,""],async_send:[2,1,1,""],async_send_block:[2,1,1,""],async_send_height:[2,1,1,""],async_send_int32:[2,1,1,""],async_send_string:[2,1,1,""],async_send_txs:[2,1,1,""],async_send_void:[2,1,1,""],cmd_to_text:[2,1,1,""]},config:{POC_LAST_BROADHASH:[2,2,1,""],POW_LEDGER_DB:[2,2,1,""]},determine:{REF_HASH:[2,2,1,""],connect_ok_from:[2,1,1,""],get_connect_to:[2,1,1,""],hn_list_to_test_slots:[2,1,1,""],hn_list_to_tickets:[2,1,1,""],my_distance:[2,1,1,""],my_hash_distance:[2,1,1,""],pick_two_not_in:[2,1,1,""],tickets_to_jurors:[2,1,1,""],timestamp_to_round_slot:[2,1,1,""]},posblock:{PosBlock:[2,3,1,""],PosHeight:[2,3,1,""],PosMessage:[2,3,1,""]},poschain:{MemoryPosChain:[2,3,1,""],PosChain:[2,3,1,""],SQL_CREATE_POS_ROUNDS:[2,2,1,""],SQL_ROUNDS_SOURCES:[2,2,1,""],SqlitePosChain:[2,3,1,""]},posclient:{Posclient:[2,3,1,""]},poscrypto:{blake:[2,1,1,""],check_sig:[2,1,1,""],gen_keys:[2,1,1,""],gen_keys_file:[2,1,1,""],hash_to_addr:[2,1,1,""],hex_to_raw:[2,1,1,""],load_keys:[2,1,1,""],pub_key_to_addr:[2,1,1,""],raw_to_hex:[2,1,1,""],sign:[2,1,1,""],validate_address:[2,1,1,""]},poshelpers:{download_file:[2,1,1,""],fake_hn_dict:[2,1,1,""],first_height_is_better:[2,1,1,""],heights_match:[2,1,1,""],hello_string:[2,1,1,""],ipport_to_fullpeer:[2,1,1,""],load_hn_temp:[2,1,1,""],peer_to_fullpeer:[2,1,1,""],same_height:[2,1,1,""],update_source:[2,1,1,""]},poshn:{HNState:[2,3,1,""],HnServer:[2,3,1,""],Poshn:[2,3,1,""],REUSE_PORT:[2,2,1,""]},posmempool:{MemoryMempool:[2,3,1,""],Mempool:[2,3,1,""],SqliteMempool:[2,3,1,""]},sqlitebase:{SqliteBase:[2,3,1,""]}},objnames:{"0":["py","module","Python module"],"1":["py","function","Python function"],"2":["py","data","Python data"],"3":["py","class","Python class"],"4":["py","method","Python method"],"5":["py","attribute","Python attribute"]},objtypes:{"0":"py:module","1":"py:function","2":"py:data","3":"py:class","4":"py:method","5":"py:attribute"},terms:{"053a53f0dffe1f":0,"0port":2,"0x7f013c023ea0":[],"0x7f0556dc7ea0":2,"0x7f0f2b254ea0":[],"0x7f21cdc75ea0":[],"0x7f6f02b1aea0":[],"0x7f8a929deea0":[],"0x7f8d3840aea0":[],"0x7faa3977aea0":[],"0x7fbd4bb93ea0":[],"10sec":2,"123456789abcdef12345":2,"2275e088ef7dde5972":0,"2275e088ef7dde597279cd":0,"27d17e8868074f84282c39f87":0,"28b828f717e4d04cad8c1b48f5d4b61a85203415":0,"323c6766c8c0267c6cb5b8d4161f1d4e0f7db0f64dd52942a086240ae9561b2d2a3e1dc91febbf83c636e7e092931e8fd96e2eb4103ba466c225128a6339f9b7":2,"34371d12bb699e97":0,"34371d12bb6c249e899e97":0,"53a53f0dffe1f":0,"67987b1589c0522":0,"72e7da47b2967":0,"74f84282c39f87":0,"7b12101dcb088170285b5d5cad68e7e79e4cb6b4":0,"7da47b2967":0,"8bdc804328d9":0,"8bdc804328d9e8ac0":0,"8bdc804328d9e8ac097fb2b2f":0,"8bdc804328d9e8ac097fb2b2f53ca5902e28f21423f1db87f4ab39a970176c6d4bb33e24b75200438a49f8308e4f6addf471b6e6591c091da5053a53f0dffe1f":0,"8cf00afce4891afe9f57":0,"9094d7b35ac3e924c20545486f75d6e10c8b1ea7":2,"abstract":1,"boolean":2,"byte":2,"case":[0,2],"class":1,"default":2,"enum":2,"final":2,"function":2,"int":2,"long":[0,2],"new":2,"null":2,"public":2,"return":[0,2],"short":0,"static":2,"switch":0,"throw":2,"true":2,"try":2,AND:[0,2],For:2,HNs:2,INTO:2,NOT:2,PoS:[0,1],Pos:1,The:2,Used:2,Uses:2,_consensu:2,_delete_tx:2,_exchange_height:2,_exchange_mempool:2,_get_peer_stream:2,_get_round_block:2,_handle_msg:2,_height_statu:2,_insert_block:2,_insert_tx:2,_invalid:2,_last_block:2,_new_tx:2,_round_sync:2,_update_network:2,a03ffeea35a48f0773bc993289213c3c72165ee0:2,a7a4b32406584b54bd30bacbe0457583a2d84492:0,a9254987127c1cc8313218a97ff700193cc:0,a9254987127c1cc8313218a97ff700193ccd16af6b535d1f143f0ecc78dc1148c7c23a8ad549c93ebfdbfbb2f8c579619ee3d65961b98cf00afce4891afe9f57:[],a_height:2,a_round:2,aa012345678901aa:2,about:0,access_log:2,action:2,activ:2,active_hn:2,adapt:2,add:[0,2],add_inbound:2,add_to_proto:2,add_to_proto_block:2,addr:2,address:2,address_list:2,adjust:2,advertis:2,ae27f98d0fc513778ce78c22287214bbbe702db3:0,after:[0,2],afterward:2,against:2,agre:2,aioevent:2,aioprocess:2,algorithm:2,all:2,allow:2,alreadi:2,also:[0,2],altern:2,alwai:[0,2],ancestor:2,answer:0,api:2,app_log:2,approv:2,archiv:2,as_dict:2,as_hex:2,assembl:2,async:2,async_active_hn:2,async_al:2,async_alltxid:2,async_blockinfo:2,async_blocksync:2,async_clos:2,async_commit:2,async_del_txid:2,async_execut:2,async_fetchal:2,async_fetchon:2,async_getaddtx:2,async_getblock:2,async_gethead:2,async_gettx:2,async_height:2,async_purg:2,async_purge_start:2,async_rec:2,async_roundblock:2,async_send:2,async_send_block:2,async_send_height:2,async_send_int32:2,async_send_str:2,async_send_tx:2,async_send_void:2,async_sinc:2,async_vacuum:2,asynchron:2,author:2,avail:2,available_log:[],avoid:[0,2],b58decod:2,b58decode_int:2,b58encod:2,b58encode_int:2,b8stx39s5nbfx746zx5dcqzpuugjqpjvic:0,back:[0,2],backend:1,base58:1,base:2,been:2,best:2,better:2,between:2,bewar:2,bhbblpbtavkrj1xdlmm48qa6xjucgofcuh:0,binari:2,bis_addr:2,blake:2,block:1,block_count:2,block_dict:2,block_hash:[0,2],block_height:2,block_proto:2,block_sync_count:0,blockheight:2,blykqwgzmwjsh7dy6hmunbptbqorqx14n:[0,2],bmsmnnzb9qddp1vudrzoge4buz1gcuc3cv:0,bnjp77d1bdoaqu9hepgjkcsgckqsxkj7fd:0,bool:2,both:0,buffer:2,build:2,bytearrai:2,c0cb310e2877d73e2f29a949aabb8fef0ea00edf:2,ca74987b1589c0522:0,calc:2,call:2,caller:2,came:2,can:[0,2],candid:2,catching_up_connect1:2,catching_up_connect2:2,catching_up_elect:2,catching_up_presync:2,catching_up_sync:2,chain:[0,1],chang:2,change_state_to:2,check:2,check_o:2,check_round:2,check_sig:2,checksum:2,cleanli:2,clear:2,client:1,client_work:2,close:2,cmd:2,cmd_to_text:2,coher:2,com_help:1,come:2,comma:0,command:2,commit:2,common:[0,2],commun:1,compar:2,config:[0,1],connect:[0,2],connect_ok_from:2,connect_to:0,connected_count:0,consensu:2,consid:0,constant:1,contain:2,content:[0,1,2],convers:2,convert:[0,2],core:1,count:[0,2],coupl:2,creat:2,crypto:1,cryptocurr:2,cryptograph:2,current:[0,2],cursor:2,d0feb58827e614f768e97fe9e9981e4b1:0,d0feb58827e614f768e97fe9e9981e4bdf91be9251066a6a0938aa8e26fd66c5aad410da2304b022a5b8e0f2672da2a28b6856727d17e8868074f84282c39f87:[],d0feb58827e614f76:0,da5053a53f0dffe1f:0,data:2,datadir:2,date:2,db_name:2,db_path:2,dc72e7da47b2967:0,debug:2,decod:2,dedic:0,delet:2,delete_round:2,depend:2,deprec:2,deriv:0,detail:0,determin:1,determinist:1,dev:2,dict:[0,2],differ:2,digest:2,digest_block:2,digest_height:2,digest_tx:2,distanc:2,distant:2,distinct:2,doe:[0,2],domain:2,doubl:2,download_fil:2,dure:2,each:[0,2],element:2,emb:2,emit:0,empti:[0,2],encod:2,end:[0,2],end_round:[0,2],error:2,establish:2,even:2,ever:2,exampl:[0,2],except:2,exchang:[0,2],execut:2,exist:2,extra:[0,2],extract:2,fake:2,fake_hn_dict:2,fals:2,fast_check:2,featur:2,fetch:2,fetch_on:2,field:2,file:2,filenam:2,fill:2,first_height_is_bett:2,fit:2,flag:2,follow:0,forg:2,forge_slot:2,forger:[0,2],forgers_round:[0,2],fork:2,format:2,found:0,fresh:2,from:[0,2],from_dict:2,from_list:2,from_min:2,from_proto:2,from_valu:2,full:[0,2],full_hn_list:2,full_peer:2,gen_kei:2,gen_keys_fil:2,gener:2,genesi:[0,2],genesis_block:2,get:[0,2],get_connect_to:2,get_hypernod:2,give:2,given:[0,2],got:2,grow:2,ham:2,handl:2,handle_stream:2,handler:2,harmon:2,has:2,hash20:2,hash:2,hash_to_addr:2,header:2,height:[0,2],height_a:2,height_b:2,height_dict:2,height_proto:2,heights_match:2,hello:2,hello_str:2,helper:1,here:2,hex:2,hex_encod:2,hex_str:2,hex_to_raw:2,hexadecim:2,his:2,hn_client:1,hn_instanc:1,hn_list:2,hn_list_to_test_slot:2,hn_list_to_ticket:2,hn_temp:2,hn_version:0,hnserver:2,hnstate:2,host:0,imag:2,impli:2,inactive_last_round:2,inbound:[0,2],includ:[0,2],inclus:0,index:[1,2],indic:2,info:[0,2],init:2,init_check:2,init_log:2,initi:2,inner:2,input:0,insert:2,insert_block:[],instanc:[1,2],instead:[0,2],int32:2,integ:2,interfac:2,invalid:2,iostream:2,ipport_to_fullp:2,iseq:2,issu:0,item:2,its:2,itself:2,json:[0,2],json_encod:2,juror:2,keep:2,kei:[0,2],know:2,larger:2,largest:2,last:2,last_block:2,later:2,latest:[0,2],ledger:2,len:2,length:2,less:2,level:2,lib_vers:0,lifespan:2,light:2,like:2,line:2,list:[0,2],live:2,load:2,load_hn_temp:2,load_kei:2,local:2,localtim:0,lock:2,log:2,low:2,lower:0,mai:2,mainten:2,manag:2,manual:2,master:2,match:[0,2],memori:2,memorymempool:2,memoryposchain:2,mempool:1,mersenn:2,messag:2,metric:[0,2],miner:2,minimal_consensu:2,mismatch:0,modifi:2,modul:1,more:2,most:[0,2],msg:2,msg_count:[0,2],my_dist:2,my_hash_dist:2,nativ:2,necessari:2,need:2,net_height:0,network:2,never:2,new_stat:2,node:2,non:2,none:2,note:[0,2],notiv:2,now:0,number:2,numer:2,object:2,often:2,old:2,old_digest_block:2,omit:0,onc:2,one:2,ones:0,onli:2,opt:2,option:2,order:2,our:2,our_statu:2,out:2,outbound:[0,2],output:[0,2],own:2,page:1,param:2,paramet:[0,2],parent:2,part:2,partial:2,peer:[0,2],peer_ip:2,peer_port:2,peer_statu:2,peer_to_fullp:2,perf:2,period:[0,2],permut:2,pick:2,pick_two_not_in:2,plenti:2,poc:2,poc_last_broadhash:2,port:2,pos:2,pos_chain:2,pos_filenam:2,pos_messag:2,pos_round:2,posblock:1,poschain:1,posclient:1,poscrypto:1,posheight:2,poshelp:1,poshn:1,posmempool:1,posmessag:2,posnet:2,post_block:2,poswallet:2,pow:2,pow_ledger_db:2,predic:2,predict:2,prefer:0,previou:0,previous_hash:[0,2],primari:2,primit:1,print:2,printabl:2,prioritari:2,priv:2,priv_kei:2,process:2,prod:2,progress:2,promised_height:2,prop:2,properti:2,proto:2,proto_block:2,proto_tx:2,protoblock:2,protobuf:2,protobuff:2,protocmd:2,provid:2,proxi:2,pseudo:1,pub:2,pub_kei:2,pub_key_to_addr:2,pubkei:2,pubkey_str:2,purg:2,purpos:2,python3:0,python:2,quickli:2,rais:2,ram:2,random:2,rang:2,raw:2,raw_to_hex:2,reach:2,readabl:2,reason:2,recalc:2,receiv:[0,2],received_bi:[0,2],recipi:[0,2],ref:2,ref_hash:2,reference_hash:2,refresh_last_block:2,regist:2,relat:1,relaxed_check:2,remov:2,remove_inbound:2,repo:2,report:0,repres:2,represent:2,request:2,requir:2,respons:2,result:2,reuse_port:2,revert:2,reward:2,rollback:2,round:2,round_statu:2,round_sync:2,routin:2,rtt:0,run:[0,2],safe:2,same_height:2,sampl:0,save:2,scale:2,scrub_input:2,search:1,sec:0,second:2,section:[0,2],select:2,self:2,send:[0,2],sender:[0,2],separ:2,sequenc:2,serv:2,server:2,set:[0,1],shall:2,share:2,shot:2,should:2,side:[0,2],sign:2,signal:2,signatur:[0,2],simpler:2,simul:2,sinc:2,singl:2,sir:[0,2],slot:[0,2],small:2,socket:2,someth:2,sort:2,sourc:2,space:2,specif:2,sql:2,sql_create_pos_round:2,sql_insert_genesi:2,sql_rounds_sourc:2,sqlite3:1,sqlite:2,sqlitebas:1,sqlitemempool:2,sqliteposchain:2,start:[0,2],start_height:2,start_round:[0,2],stat:[0,2],state:[0,2],statu:2,statustim:0,stop:2,stop_ev:2,storag:2,store:2,str:2,stream:2,string:[0,2],strong_consensu:2,structur:2,sub:2,success:2,suffix:2,supposedli:2,sync:2,tabl:2,take:2,tbd:2,tcp:2,tcpserver:2,tell:2,temp:2,termin:2,test:[0,2],test_slot:[0,2],text:2,tgz:2,than:2,thei:2,them:2,thi:2,think:2,those:2,thread:2,ticker:2,ticket:2,tickets_list:2,tickets_to_juror:2,time:[0,2],timestamp:[0,2],timestamp_to_round_slot:2,to_db:2,to_dict:2,to_json:2,to_list:2,to_proto:2,to_raw:2,todo:[0,2],too:2,tool:2,tornado:2,total:2,transact:[0,2],tri:2,trip:0,tuneabl:2,tupl:2,twister:2,tx_count:2,tx_dict:2,tx_exist:2,tx_list:2,txid:2,txs:[0,2],type:2,unabl:2,uniqu:[0,2],unique_sourc:[0,2],uniques_round:[0,2],uniques_sourc:2,until:2,updat:2,update_inbound:2,update_sourc:2,upper:0,urgent:2,url:2,use:[0,2],used:2,user:2,uses:2,using:2,util:1,vacuum:2,valid:2,validate_address:2,valu:2,valueerror:2,variabl:2,variou:2,verbos:2,verifi:2,version:2,via:0,wallet:2,want:2,warn:2,weight:[0,2],well:0,what:2,when:2,where:[0,2],which:2,whole:[0,2],wip:[0,2],with_tx:2,within:2,without:[0,2],worker:2,yet:[0,2],you:2,zfill:2},titles:["&gt; Bismuth Hypernodes","Welcome to Bismuth Hypernodes\u2019s documentation!","&gt; Modules"],titleterms:{"abstract":2,"class":2,"default":0,PoS:2,Pos:2,action:0,address:0,address_tx:0,argument:0,backend:2,base58:2,basic:0,bismuth:[0,1,2],block:[0,2],block_height:0,blocksync:0,chain:2,client:[0,2],com_help:2,command:0,commun:2,config:2,constant:2,core:2,crypto:2,determin:2,determinist:2,document:1,fals:0,header:0,hello:0,helper:2,hn_client:0,hn_instanc:0,hypernod:[0,1,2],index:0,indic:1,instanc:0,line:0,mempool:[0,2],modul:2,option:0,param:0,ping:0,port:0,posblock:2,poschain:2,posclient:2,poscrypto:2,poshelp:2,poshn:2,posmempool:2,primit:2,pseudo:2,relat:2,round:0,set:2,sqlite3:2,sqlitebas:2,statu:0,tabl:1,tx_signatur:0,txtest:0,util:2,verbos:0,version:0,welcom:1}})